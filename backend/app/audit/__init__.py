"""Registro de auditoría: un evento por cada paso del proceso, proyectable a AuditEvent FHIR."""

from app.audit.registro import EventoAuditoria, Resultado, registrar

__all__ = ["EventoAuditoria", "Resultado", "registrar"]
