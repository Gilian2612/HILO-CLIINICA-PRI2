"""Gestor de consentimiento.

La paciente autoriza por categorías; cada categoría habilita ciertos tipos de recurso FHIR.
El permiso dura 24 horas, puede abrirse por emergencia y puede revocarse.
Regla central: un tipo de recurso solo se consulta si hay un Consent activo que lo incluye.
"""

from app.consent.categorias import CATEGORIAS, TODAS, Categoria, tipos_de
from app.consent.consulta import Peticion, ResultadoConsulta, consultar_red
from app.consent.gestor import crear_consentimiento, permite, revocar

__all__ = [
    "CATEGORIAS",
    "TODAS",
    "Categoria",
    "Peticion",
    "ResultadoConsulta",
    "consultar_red",
    "crear_consentimiento",
    "permite",
    "revocar",
    "tipos_de",
]
