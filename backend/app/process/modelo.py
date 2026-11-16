"""Modelo del proceso BPMN TO-BE: atención de urgencias con Hilo Clínico.

Las coordenadas (cx, cy, puntos) son las del diagrama original y las usa el frontend
para dibujarlo. La lógica del proceso está en `siguiente()`.
"""

from dataclasses import dataclass, field
from typing import Literal

Kind = Literal["start", "end", "user", "service", "send", "xor"]


@dataclass(frozen=True)
class Carril:
    id: str
    nombre: str


@dataclass(frozen=True)
class Nodo:
    id: str
    kind: Kind
    carril: str
    nombre: str
    cx: int
    cy: int
    ayuda: str = ""
    label_at: tuple[int, int] | None = None


@dataclass(frozen=True)
class Flujo:
    id: str
    desde: str
    hacia: str
    puntos: tuple[tuple[int, int], ...]
    nombre: str = ""
    label_at: tuple[int, int] | None = None


@dataclass(frozen=True)
class Mensaje:
    """Flujo de mensaje hacia o desde un pool externo (línea punteada)."""

    id: str
    desde: str
    hacia: str
    puntos: tuple[tuple[int, int], ...]
    nombre: str
    label_at: tuple[int, int] | None = None


CARRILES: list[Carril] = [
    Carril("lane_medico", "Médico de urgencias"),
    Carril("lane_hilo", "Hilo Clínico"),
    Carril("lane_paciente", "Paciente"),
]

POOLS: list[Carril] = [
    Carril("pool_fuentes", "Sistemas de la red: EPS, IPS y laboratorios"),
    Carril("pool_ihce", "IHCE del Ministerio de Salud"),
]

_NODOS: list[Nodo] = [
    Nodo("start", "start", "lane_medico", "Llega a urgencias", 112, 75),
    Nodo(
        "t_buscar", "user", "lane_medico", "Buscar paciente por documento", 205, 75,
        "El médico escribe el documento en el visor. Si es una urgencia vital, lo marca.",
    ),
    Nodo(
        "t_mpi", "service", "lane_hilo", "Identificar en índice maestro", 345, 235,
        "El índice maestro reconoce a la misma persona en la EPS, la IPS y el laboratorio, "
        "aunque cada uno la guarde distinto.",
    ),
    Nodo(
        "g_urg", "xor", "lane_hilo", "¿Urgencia vital?", 445, 235,
        "Si la paciente no puede responder, el acceso se abre de inmediato y queda auditado.",
        (445, 276),
    ),
    Nodo(
        "t_emerg", "service", "lane_hilo", "Abrir acceso de emergencia", 555, 165,
        "Acceso sin autorización previa, limitado a 24 horas. La paciente recibe el aviso.",
    ),
    Nodo(
        "t_solic", "send", "lane_hilo", "Pedir permiso a la paciente", 555, 235,
        "El gestor de consentimiento envía la solicitud a la app de la paciente.",
    ),
    Nodo(
        "t_resp", "user", "lane_paciente", "Responder solicitud en la app", 695, 385,
        "La paciente decide qué puede ver el médico y por cuánto tiempo.",
    ),
    Nodo(
        "g_aut", "xor", "lane_hilo", "¿Autoriza?", 800, 235,
        "Sin autorización no se consulta ninguna fuente.", (800, 200),
    ),
    Nodo(
        "end_no", "end", "lane_hilo", "Acceso denegado", 800, 305,
        "El médico atiende con lo que la paciente le cuente. El rechazo queda en la auditoría.",
        (868, 306),
    ),
    Nodo("g_join", "xor", "lane_hilo", "", 880, 235),
    Nodo(
        "t_fhir", "service", "lane_hilo", "Traer y unir datos vía FHIR", 980, 235,
        "Los adaptadores consultan cada fuente y traducen su formato a recursos HL7 FHIR.",
    ),
    Nodo(
        "t_atender", "user", "lane_medico", "Revisar historia y atender", 1120, 75,
        "El médico ve alergias, consultas y exámenes en una sola línea de tiempo.",
    ),
    Nodo(
        "g_dest", "xor", "lane_hilo", "¿Dónde se registra?", 1230, 235,
        "Según lo que elija el médico o la configuración de la IPS, la atención se guarda en "
        "Hilo Clínico o se envía al sistema propio de la IPS.",
        (1160, 300),
    ),
    Nodo(
        "t_guardar", "service", "lane_hilo", "Guardar en Hilo Clínico", 1345, 170,
        "La atención queda guardada en Hilo Clínico.",
    ),
    Nodo(
        "t_envio", "service", "lane_hilo", "Enviar atención vía FHIR a la IPS", 1345, 290,
        "El adaptador arma un Bundle FHIR de tipo transaction y lo envía por POST al endpoint "
        "de la IPS. Hilo Clínico guarda solo la referencia.",
    ),
    Nodo("g_dj", "xor", "lane_hilo", "", 1455, 235),
    Nodo(
        "t_cerrar", "service", "lane_hilo", "Auditar y enviar RDA", 1550, 235,
        "Se registra el acceso en la auditoría y se envía el Resumen Digital de Atención al IHCE.",
    ),
    Nodo("end_ok", "end", "lane_hilo", "Atención registrada", 1650, 235, "", (1650, 272)),
]

NODOS: dict[str, Nodo] = {n.id: n for n in _NODOS}

FLUJOS: list[Flujo] = [
    Flujo("f1", "start", "t_buscar", ((128, 75), (150, 75))),
    Flujo("f2", "t_buscar", "t_mpi", ((260, 75), (275, 75), (275, 235), (290, 235))),
    Flujo("f3", "t_mpi", "g_urg", ((400, 235), (423, 235))),
    Flujo("f4", "g_urg", "t_solic", ((467, 235), (500, 235)), "No", (482, 226)),
    Flujo("f5", "g_urg", "t_emerg", ((445, 213), (445, 165), (500, 165)), "Sí", (456, 192)),
    Flujo("f6", "t_solic", "t_resp", ((610, 235), (625, 235), (625, 385), (640, 385))),
    Flujo("f7", "t_resp", "g_aut", ((695, 357), (695, 235), (778, 235))),
    Flujo("f8", "g_aut", "g_join", ((822, 235), (858, 235)), "Sí", (840, 226)),
    Flujo("f9", "g_aut", "end_no", ((800, 257), (800, 289)), "No", (813, 276)),
    Flujo("f10", "t_emerg", "g_join", ((610, 165), (880, 165), (880, 213))),
    Flujo("f11", "g_join", "t_fhir", ((902, 235), (925, 235))),
    Flujo("f12", "t_fhir", "t_atender", ((1035, 235), (1050, 235), (1050, 75), (1065, 75))),
    Flujo("f13", "t_atender", "g_dest", ((1175, 75), (1190, 75), (1190, 235), (1208, 235))),
    Flujo("f15", "g_dest", "t_guardar", ((1230, 213), (1230, 170), (1290, 170)), "Hilo Clínico", (1258, 161)),
    Flujo("f16", "g_dest", "t_envio", ((1230, 257), (1230, 290), (1290, 290)), "IPS", (1258, 281)),
    Flujo("f17", "t_guardar", "g_dj", ((1400, 170), (1455, 170), (1455, 213))),
    Flujo("f18", "t_envio", "g_dj", ((1400, 290), (1455, 290), (1455, 257))),
    Flujo("f19", "g_dj", "t_cerrar", ((1477, 235), (1495, 235))),
    Flujo("f14", "t_cerrar", "end_ok", ((1605, 235), (1634, 235))),
]

MENSAJES: list[Mensaje] = [
    Mensaje("m1", "t_fhir", "pool_fuentes", ((962, 263), (962, 475)), "Consulta FHIR", (918, 456)),
    Mensaje("m2", "pool_fuentes", "t_fhir", ((998, 475), (998, 263)), "Recursos", (1030, 456)),
    Mensaje("m3", "t_cerrar", "pool_ihce", ((1550, 263), (1550, 475)), "RDA", (1572, 456)),
    Mensaje("m4", "t_envio", "pool_fuentes", ((1325, 318), (1325, 475)), "Bundle FHIR", (1282, 456)),
    Mensaje("m5", "pool_fuentes", "t_envio", ((1365, 475), (1365, 318)), "201 Created", (1408, 456)),
]


def flujo_entre(desde: str, hacia: str) -> Flujo | None:
    return next((f for f in FLUJOS if f.desde == desde and f.hacia == hacia), None)


def siguiente(
    nodo: str,
    *,
    emergencia: bool = False,
    decision: str | None = None,
    destino: str = "hilo",
) -> str | None:
    """A qué nodo se pasa desde `nodo`. Las compuertas deciden con el contexto."""
    match nodo:
        case "start":
            return "t_buscar"
        case "t_buscar":
            return "t_mpi"
        case "t_mpi":
            return "g_urg"
        case "g_urg":
            return "t_emerg" if emergencia else "t_solic"
        case "t_emerg":
            return "g_join"
        case "t_solic":
            return "t_resp"
        case "t_resp":
            return "g_aut"
        case "g_aut":
            return "g_join" if decision == "granted" else "end_no"
        case "g_join":
            return "t_fhir"
        case "t_fhir":
            return "t_atender"
        case "t_atender":
            return "g_dest"
        case "g_dest":
            return "t_envio" if destino == "ips" else "t_guardar"
        case "t_guardar" | "t_envio":
            return "g_dj"
        case "g_dj":
            return "t_cerrar"
        case "t_cerrar":
            return "end_ok"
        case _:
            return None
