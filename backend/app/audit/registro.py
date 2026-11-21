"""Eventos de auditoría.

El dominio guarda un registro simple (quién, qué, detalle, resultado, hora). Cuando hace
falta intercambiarlo, `a_fhir()` lo proyecta a un AuditEvent R4 válido.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from fhir.resources.R4B.auditevent import AuditEvent

Resultado = Literal["ok", "warn", "deny"]

TIPO_EVENTO = "http://dicom.nema.org/resources/ontology/DCM"
OUTCOME = {"ok": "0", "warn": "0", "deny": "4"}  # códigos FHIR: 0 éxito, 4 fallo menor


@dataclass(frozen=True)
class EventoAuditoria:
    id: str
    hora: datetime
    quien: str
    accion: str
    detalle: str
    resultado: Resultado

    def a_fhir(self) -> AuditEvent:
        return AuditEvent(
            id=self.id,
            type={"system": TIPO_EVENTO, "code": "110110", "display": "Patient Record"},
            action="E",
            recorded=self.hora,
            outcome=OUTCOME[self.resultado],
            outcomeDesc=self.resultado,
            agent=[{"who": {"display": self.quien}, "requestor": True}],
            source={"observer": {"display": "Hilo Clínico"}},
            entity=[{"name": self.accion, "description": self.detalle}],
        )


def registrar(
    hora: datetime, quien: str, accion: str, detalle: str, resultado: Resultado = "ok"
) -> EventoAuditoria:
    """Crea un evento con un id determinista (misma hora y acción → mismo id)."""
    return EventoAuditoria(
        id=f"aud-{hora:%H%M%S}-{_hash31(accion + detalle) % 997}",
        hora=hora,
        quien=quien,
        accion=accion,
        detalle=detalle,
        resultado=resultado,
    )


def _hash31(texto: str) -> int:
    """Hash estable (no depende de PYTHONHASHSEED), el mismo que usaba el boceto."""
    h = 0
    for c in texto:
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return h
