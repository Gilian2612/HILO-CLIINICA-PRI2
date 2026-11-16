"""Adaptadores: traducen cada fuente nativa a recursos FHIR R4.

Cada adaptador declara los tipos de recurso que produce. Eso lo usa el gestor de
consentimiento para saber qué se puede pedir a cada fuente.
"""

from collections.abc import Callable
from dataclasses import dataclass

from fhir.resources.R4B.resource import Resource

from app.adapters import eps, ips, lab
from app.mpi import PacienteMaestro


@dataclass(frozen=True)
class Adaptador:
    fuente: str
    tipos: tuple[str, ...]
    a_fhir: Callable[[PacienteMaestro], list[Resource]]


ADAPTADORES: dict[str, Adaptador] = {
    "eps": Adaptador("eps", ("Coverage", "ServiceRequest"), eps.a_fhir),
    "ips": Adaptador(
        "ips", ("AllergyIntolerance", "Encounter", "Condition", "MedicationRequest"), ips.a_fhir
    ),
    "lab": Adaptador("lab", ("Observation",), lab.a_fhir),
}

__all__ = ["ADAPTADORES", "Adaptador", "eps", "ips", "lab"]
