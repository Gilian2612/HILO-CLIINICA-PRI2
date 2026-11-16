"""Máquina de estados que recorre el proceso.

Estados de la simulación:
- waiting: en una tarea de usuario, esperando que el médico o la paciente actúen.
- running: en una tarea de servicio o compuerta (su efecto ya se ejecutó al llegar).
- moving:  el token va por un flujo hacia el siguiente nodo (el frontend lo anima).
- ended:   en un evento de fin.

Transiciones: actuar() en waiting → moving · completar() en running → moving ·
llegar() en moving → waiting | running | ended. paso() hace la que toque.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal

from fhir.resources.R4B.bundle import Bundle
from fhir.resources.R4B.consent import Consent
from fhir.resources.R4B.resource import Resource

from app.actores import MEDICO
from app.audit import EventoAuditoria, Resultado, registrar
from app.consent import TODAS, Peticion, consultar_red, crear_consentimiento, revocar
from app.fhir import ENDPOINT_IPS, LineaTiempo, crear_envio_ips, crear_rda, linea_de_tiempo
from app.mpi import DocumentoCorto, PacienteNoEncontrado, ResultadoBusqueda, buscar
from app.process.modelo import NODOS, flujo_entre, siguiente
from app.sources import FUENTES

Escenario = Literal["consentimiento", "emergencia", "rechazo"]
Estado = Literal["waiting", "running", "moving", "ended"]

ESCENARIOS = [
    {"id": "consentimiento", "label": "Con autorización", "blurb": "Mariana autoriza desde su app."},
    {"id": "emergencia", "label": "Urgencia vital", "blurb": "Mariana no puede responder: acceso de emergencia."},
    {"id": "rechazo", "label": "Mariana no autoriza", "blurb": "Sin permiso no se consulta nada."},
]

NOTA_POR_DEFECTO = (
    "Antecedentes revisados en Hilo Clínico: alergia a la penicilina y exámenes del "
    "7 de noviembre. No se repiten hemograma ni proteína C reactiva."
)
ZONA_COLOMBIA = timezone(timedelta(hours=-5))


@dataclass
class Borrador:
    """Lo que el usuario tiene escrito en pantalla antes de actuar."""

    documento: str = "1032456789"
    emergencia: bool = False
    categorias: list[str] = field(default_factory=lambda: list(TODAS))
    nota: str = NOTA_POR_DEFECTO
    destino: str = "hilo"


@dataclass
class Contexto:
    """Todo lo que el proceso va produciendo."""

    borrador: Borrador = field(default_factory=Borrador)
    error_busqueda: str | None = None
    emergencia: bool = False
    mpi: ResultadoBusqueda | None = None
    solicitud: str | None = None  # pending | granted | denied
    decision: str | None = None  # granted | denied
    consent: Consent | None = None
    revocado: bool = False
    log: list[Peticion] = field(default_factory=list)
    recursos: list[Resource] = field(default_factory=list)
    linea: LineaTiempo | None = None
    nota: str = ""
    destino: str = "hilo"
    rda: Bundle | None = None
    envio: Bundle | None = None
    auditoria: list[EventoAuditoria] = field(default_factory=list)
    reloj: int = 0  # segundos transcurridos desde el inicio


@dataclass
class Movimiento:
    flujo: str
    desde: str
    hacia: str


@dataclass
class Simulacion:
    escenario: Escenario
    inicio: datetime
    nodo: str
    estado: Estado
    visitados: list[str]
    flujos: list[str]
    ctx: Contexto
    en_movimiento: Movimiento | None = None

    def ahora(self) -> datetime:
        return self.inicio + timedelta(seconds=self.ctx.reloj)


def nueva_simulacion(escenario: Escenario, inicio: datetime | None = None) -> Simulacion:
    return Simulacion(
        escenario=escenario,
        inicio=inicio or datetime.now(ZONA_COLOMBIA),
        nodo="t_buscar",
        estado="waiting",
        visitados=["start", "t_buscar"],
        flujos=["f1"],
        ctx=Contexto(borrador=Borrador(emergencia=escenario == "emergencia")),
    )


# Transiciones


def actuar(sim: Simulacion, **payload) -> Simulacion:
    """El médico o la paciente actúan en la tarea de usuario actual."""
    if sim.estado != "waiting":
        return sim
    ctx, borrador = sim.ctx, sim.ctx.borrador

    if sim.nodo == "t_buscar":
        documento = payload.get("documento", borrador.documento)
        try:
            ctx.mpi = buscar(documento)
        except DocumentoCorto:
            ctx.error_busqueda = "corto"
            return sim
        except PacienteNoEncontrado:
            ctx.error_busqueda = "no-existe"
            return sim
        ctx.error_busqueda = None
        ctx.emergencia = payload.get("emergencia", borrador.emergencia)

    elif sim.nodo == "t_resp":
        paciente = ctx.mpi.paciente
        decision = payload.get("decision", "granted")
        categorias = payload.get("categorias", borrador.categorias)
        if decision == "granted":
            hora = _avanzar(sim, 9)
            ctx.decision, ctx.solicitud = "granted", "granted"
            ctx.consent = crear_consentimiento(paciente, categorias, "paciente", hora)
            _auditar(
                sim, hora, paciente.nombre, "Autorización concedida",
                f"Por 24 horas: {len(categorias)} de {len(TODAS)} tipos de información", "ok",
            )
        else:
            ctx.decision, ctx.solicitud = "denied", "denied"
            _auditar(
                sim, _avanzar(sim, 9), paciente.nombre, "Solicitud rechazada",
                "La paciente no autorizó el acceso", "deny",
            )

    elif sim.nodo == "t_atender":
        ctx.nota = payload.get("nota", borrador.nota)
        ctx.destino = payload.get("destino", borrador.destino)

    return _salir(sim)


def completar(sim: Simulacion) -> Simulacion:
    """Una tarea de servicio o compuerta termina y el token sale por su flujo."""
    return _salir(sim) if sim.estado == "running" else sim


def llegar(sim: Simulacion) -> Simulacion:
    """El token llega al siguiente nodo y se ejecuta su efecto."""
    if sim.estado != "moving" or sim.en_movimiento is None:
        return sim
    destino = sim.en_movimiento.hacia
    sim.nodo = destino
    sim.visitados.append(destino)
    sim.flujos.append(sim.en_movimiento.flujo)
    sim.en_movimiento = None
    _efecto(sim, destino)
    kind = NODOS[destino].kind
    sim.estado = "ended" if kind == "end" else "waiting" if kind == "user" else "running"
    return sim


def paso(sim: Simulacion) -> Simulacion:
    """Hace la transición que corresponda; en tareas de usuario usa la respuesta del escenario."""
    match sim.estado:
        case "waiting":
            return actuar(sim, **_respuesta_del_escenario(sim))
        case "running":
            return completar(sim)
        case "moving":
            return llegar(sim)
        case _:
            return sim


def correr(
    sim: Simulacion | Escenario, inicio: datetime | None = None, hasta: str | None = None
) -> Simulacion:
    """Avanza hasta el fin, o hasta quedar esperando en la tarea de usuario `hasta`."""
    if isinstance(sim, str):
        sim = nueva_simulacion(sim, inicio)
    for _ in range(200):
        if sim.estado == "ended":
            break
        if hasta and sim.nodo == hasta and sim.estado == "waiting":
            break
        paso(sim)
    return sim


def revocar_acceso(sim: Simulacion) -> Simulacion:
    """La paciente revoca desde su app. A partir de ahí el médico no ve nada."""
    ctx = sim.ctx
    if ctx.consent is None or ctx.consent.status != "active":
        return sim
    ctx.consent = revocar(ctx.consent)
    ctx.revocado = True
    _auditar(
        sim, _avanzar(sim, 5), ctx.mpi.paciente.nombre, "Acceso revocado",
        "La historia dejó de estar visible para el médico", "deny",
    )
    return sim


# Internos


def _salir(sim: Simulacion) -> Simulacion:
    ctx = sim.ctx
    proximo = siguiente(
        sim.nodo, emergencia=ctx.emergencia, decision=ctx.decision, destino=ctx.destino
    )
    if proximo is None:
        sim.estado = "ended"
        return sim
    flujo = flujo_entre(sim.nodo, proximo)
    sim.en_movimiento = Movimiento(flujo.id, sim.nodo, proximo)
    sim.estado = "moving"
    return sim


def _respuesta_del_escenario(sim: Simulacion) -> dict:
    if sim.nodo == "t_resp":
        return {"decision": "denied" if sim.escenario == "rechazo" else "granted"}
    return {}


def _avanzar(sim: Simulacion, segundos: int) -> datetime:
    sim.ctx.reloj += segundos
    return sim.ahora()


def _auditar(
    sim: Simulacion, hora: datetime, quien: str, accion: str, detalle: str, resultado: Resultado
) -> None:
    sim.ctx.auditoria.append(registrar(hora, quien, accion, detalle, resultado))


def _efecto(sim: Simulacion, nodo: str) -> None:
    """Lo que Hilo Clínico hace al llegar a cada nodo de servicio (o de fin)."""
    ctx = sim.ctx
    paciente = ctx.mpi.paciente if ctx.mpi else None

    match nodo:
        case "t_mpi":
            _auditar(
                sim, _avanzar(sim, 2), MEDICO.nombre, "Búsqueda en índice maestro",
                f"{paciente.documento_label}: {len(ctx.mpi.identidades)} registros unidos en 1 paciente",
                "ok",
            )

        case "t_emerg":
            hora = _avanzar(sim, 2)
            ctx.consent = crear_consentimiento(paciente, TODAS, "emergencia", hora)
            _auditar(
                sim, hora, MEDICO.nombre, "Acceso de emergencia abierto",
                "Urgencia vital declarada. Acceso por 24 horas, sin autorización previa.", "warn",
            )

        case "t_solic":
            ctx.solicitud = "pending"
            _auditar(
                sim, _avanzar(sim, 2), "Gestor de consentimiento", "Solicitud enviada a la paciente",
                f"{MEDICO.nombre} pide ver la historia de {paciente.nombres}", "ok",
            )

        case "end_no":
            _auditar(
                sim, _avanzar(sim, 1), "Gestor de consentimiento", "Acceso denegado",
                "No se consultó ninguna fuente.", "deny",
            )

        case "t_fhir":
            resultado = consultar_red(paciente, ctx.consent, sim.ahora())
            ctx.log = resultado.log
            ctx.recursos = resultado.recursos
            ctx.linea = linea_de_tiempo(ctx.recursos, sim.ahora().date())
            for fuente in ("eps", "ips", "lab"):
                entregados = sum(1 for p in resultado.log if p.fuente == fuente for _ in range(p.cantidad))
                bloqueadas = sum(1 for p in resultado.log if p.fuente == fuente and p.status == 403)
                if entregados:
                    detalle = f"{entregados} recursos entregados a {MEDICO.nombre}"
                elif bloqueadas:
                    detalle = "Fuera del permiso de la paciente: no se consultó"
                else:
                    detalle = "Sin registros"
                _auditar(
                    sim, _avanzar(sim, 1), "Adaptador FHIR", f"Consulta a {FUENTES[fuente].nombre}",
                    detalle, "ok" if entregados else "deny",
                )

        case "t_guardar":
            hora = _avanzar(sim, 4)
            ctx.rda = crear_rda(paciente, ctx.nota, hora, ctx.recursos)
            _auditar(
                sim, hora, MEDICO.nombre, "Atención guardada",
                f"En Hilo Clínico. Urgencias, {MEDICO.organizacion} ({MEDICO.ciudad})", "ok",
            )

        case "t_envio":
            hora = _avanzar(sim, 4)
            ctx.rda = crear_rda(paciente, ctx.nota, hora, ctx.recursos)
            ctx.envio = crear_envio_ips(ctx.rda, hora)
            cantidad = len(ctx.envio.entry)
            ctx.log.append(Peticion("dest", "Bundle", "POST", ENDPOINT_IPS, 201, cantidad))
            _auditar(
                sim, hora, "Adaptador FHIR", "Atención enviada al sistema de la IPS",
                f"POST de un Bundle con {cantidad} recursos a {ENDPOINT_IPS}: 201 Created "
                "(envío simulado). Hilo Clínico guarda solo la referencia.",
                "ok",
            )

        case "t_cerrar":
            if ctx.rda is None:
                ctx.rda = crear_rda(paciente, ctx.nota, _avanzar(sim, 4), ctx.recursos)
            _auditar(
                sim, _avanzar(sim, 2), "Hilo Clínico", "RDA enviado al IHCE",
                "Resumen Digital de Atención recibido (envío simulado)", "ok",
            )
