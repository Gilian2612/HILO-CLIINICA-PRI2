"""Rutas HTTP de Hilo Clínico."""

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Response, status

from app.actores import MEDICO, MEDICOS
from app.api.almacen import Entrada, almacen
from app.api.esquemas import Accion, CambioBorrador, CrearSimulacion, serializar_medico
from app.casos import CASOS
from app.consent import CATEGORIAS
from app.fhir import ENDPOINT_IPS, RED_IPS
from app.process import (
    CARRILES,
    ESCENARIOS,
    FLUJOS,
    MENSAJES,
    NODOS,
    POOLS,
    actuar,
    nueva_simulacion,
    paso,
    revocar_acceso,
)
from app.sources import FUENTES

router = APIRouter(prefix="/api")


# Catálogos (solo lectura)


@router.get("/proceso")
def proceso() -> dict:
    """El modelo BPMN, para que el frontend dibuje el diagrama y la ayuda de cada nodo."""
    return {
        "carriles": [asdict(c) for c in CARRILES],
        "pools": [asdict(p) for p in POOLS],
        "nodos": [asdict(n) for n in NODOS.values()],
        "flujos": [asdict(f) for f in FLUJOS],
        "mensajes": [asdict(m) for m in MENSAJES],
        "escenarios": ESCENARIOS,
    }


@router.get("/catalogo")
def catalogo() -> dict:
    """Fuentes, categorías de consentimiento, médico de turno, médicos, casos y red de IPS."""
    return {
        "fuentes": [asdict(f) for f in FUENTES.values()],
        "categorias": [asdict(c) for c in CATEGORIAS],
        "medico": serializar_medico(MEDICO),
        "medicos": [serializar_medico(m) for m in MEDICOS.values()],
        "casos": [asdict(c) for c in CASOS],
        "red": {"endpoint": ENDPOINT_IPS, "ips": [asdict(i) for i in RED_IPS]},
    }


# Simulaciones


def _entrada(id: str) -> Entrada:
    entrada = almacen.obtener(id)
    if entrada is None:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    return entrada


@router.post("/simulaciones", status_code=status.HTTP_201_CREATED)
def crear_simulacion(cuerpo: CrearSimulacion) -> dict:
    id = almacen.crear(nueva_simulacion(cuerpo.escenario, cuerpo.inicio, cuerpo.medico))
    return almacen.serializar(id, _entrada(id))


@router.get("/simulaciones/{id}")
def ver_simulacion(id: str) -> dict:
    return almacen.serializar(id, _entrada(id))


@router.delete("/simulaciones/{id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_simulacion(id: str) -> Response:
    _entrada(id)
    almacen.borrar(id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/simulaciones/{id}/paso")
def dar_paso(id: str) -> dict:
    """Hace la transición que toque (en tareas de usuario usa la respuesta del escenario)."""
    entrada = _entrada(id)
    almacen.mutar(entrada, paso)
    return almacen.serializar(id, entrada)


@router.post("/simulaciones/{id}/actuar")
def actuar_en_tarea(id: str, cuerpo: Accion) -> dict:
    """El médico o la paciente actúan en la tarea de usuario actual."""
    entrada = _entrada(id)
    datos = cuerpo.model_dump(exclude_unset=True)
    almacen.mutar(entrada, lambda sim: actuar(sim, **datos))
    return almacen.serializar(id, entrada)


@router.post("/simulaciones/{id}/revocar")
def revocar(id: str) -> dict:
    entrada = _entrada(id)
    almacen.mutar(entrada, revocar_acceso)
    return almacen.serializar(id, entrada)


@router.post("/simulaciones/{id}/atras")
def volver_atras(id: str) -> dict:
    entrada = _entrada(id)
    almacen.atras(entrada)
    return almacen.serializar(id, entrada)


@router.patch("/simulaciones/{id}/borrador")
def editar_borrador(id: str, cuerpo: CambioBorrador) -> dict:
    """Cambia lo que el usuario tiene escrito, sin mover el proceso ni entrar al historial."""
    entrada = _entrada(id)
    cambios = cuerpo.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(entrada.sim.ctx.borrador, campo, valor)
    if "documento" in cambios:
        entrada.sim.ctx.error_busqueda = None
    return almacen.serializar(id, entrada)
