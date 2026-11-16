"""Categorías que la paciente ve en su app y los tipos FHIR que habilita cada una."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Categoria:
    id: str
    etiqueta: str
    tipos: tuple[str, ...]


CATEGORIAS: list[Categoria] = [
    Categoria("alergias", "Alergias y medicamentos", ("AllergyIntolerance", "MedicationRequest")),
    Categoria("laboratorios", "Exámenes de laboratorio", ("Observation",)),
    Categoria("consultas", "Consultas anteriores", ("Encounter", "Condition")),
    Categoria("eps", "Afiliación y autorizaciones de tu EPS", ("Coverage", "ServiceRequest")),
]

TODAS: list[str] = [c.id for c in CATEGORIAS]


def tipos_de(ids: list[str]) -> list[str]:
    """Tipos de recurso FHIR que habilitan las categorías elegidas, en orden."""
    return [tipo for c in CATEGORIAS if c.id in ids for tipo in c.tipos]
