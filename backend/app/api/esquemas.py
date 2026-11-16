"""Cuerpos de las peticiones y serialización de la simulación a JSON.

El frontend recibe todo listo para pintar: los recursos FHIR como JSON estándar y el
resto del contexto como diccionarios planos.
"""

from dataclasses import asdict
from datetime import datetime
from typing import Any, Literal

from fhir.resources.R4B.resource import Resource
from pydantic import BaseModel

from app.fhir import LineaTiempo
from app.process import Escenario, Simulacion

# Peticiones


class CrearSimulacion(BaseModel):
    escenario: Escenario = "consentimiento"
    inicio: datetime | None = None


class Accion(BaseModel):
    """Lo que el médico o la paciente envían al actuar. Solo se usan los campos enviados."""

    documento: str | None = None
    emergencia: bool | None = None
    decision: Literal["granted", "denied"] | None = None
    categorias: list[str] | None = None
    nota: str | None = None
    destino: Literal["hilo", "ips"] | None = None


class CambioBorrador(BaseModel):
    documento: str | None = None
    emergencia: bool | None = None
    categorias: list[str] | None = None
    nota: str | None = None
    destino: Literal["hilo", "ips"] | None = None


# Serialización


def fhir_json(recurso: Resource | None) -> dict | None:
    return None if recurso is None else recurso.model_dump(mode="json", by_alias=True, exclude_none=True)


def serializar_linea(linea: LineaTiempo | None) -> dict | None:
    if linea is None:
        return None
    return {
        "items": [
            {
                **{k: v for k, v in asdict(item).items() if k != "recursos"},
                "recursos": [fhir_json(r) for r in item.recursos],
            }
            for item in linea.items
        ],
        "alergias": [
            {
                "sustancia": a.sustancia,
                "reaccion": a.reaccion,
                "critica": a.critica,
                "desde": a.desde,
                "fuente": a.fuente,
                "recurso": fhir_json(a.recurso),
            }
            for a in linea.alergias
        ],
        "cobertura": fhir_json(linea.cobertura),
    }


def serializar_simulacion(id: str, sim: Simulacion, puede_volver: bool) -> dict[str, Any]:
    ctx = sim.ctx
    return {
        "id": id,
        "escenario": sim.escenario,
        "inicio": sim.inicio.isoformat(),
        "ahora": sim.ahora().isoformat(),
        "nodo": sim.nodo,
        "estado": sim.estado,
        "visitados": list(sim.visitados),
        "flujos": list(sim.flujos),
        "en_movimiento": asdict(sim.en_movimiento) if sim.en_movimiento else None,
        "puede_volver": puede_volver,
        "ctx": {
            "borrador": asdict(ctx.borrador),
            "error_busqueda": ctx.error_busqueda,
            "emergencia": ctx.emergencia,
            "mpi": asdict(ctx.mpi) if ctx.mpi else None,
            "solicitud": ctx.solicitud,
            "decision": ctx.decision,
            "consent": fhir_json(ctx.consent),
            "revocado": ctx.revocado,
            "log": [asdict(p) for p in ctx.log],
            "recursos": [fhir_json(r) for r in ctx.recursos],
            "linea": serializar_linea(ctx.linea),
            "nota": ctx.nota,
            "destino": ctx.destino,
            "rda": fhir_json(ctx.rda),
            "envio": fhir_json(ctx.envio),
            "auditoria": [
                {
                    "id": e.id,
                    "hora": e.hora.isoformat(),
                    "quien": e.quien,
                    "accion": e.accion,
                    "detalle": e.detalle,
                    "resultado": e.resultado,
                }
                for e in ctx.auditoria
            ],
            "reloj": ctx.reloj,
        },
    }
