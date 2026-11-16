"""Actores fijos de la simulación (datos ficticios)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Profesional:
    id: str
    nombre: str
    rol: str
    organizacion: str
    ciudad: str

    @property
    def display(self) -> str:
        """Cómo aparece en los recursos FHIR: 'Dr. Mateo Vargas, Clínica del Pacífico'."""
        return f"{self.nombre}, {self.organizacion}"


MEDICO = Profesional(
    id="prac-0192",
    nombre="Dr. Mateo Vargas",
    rol="Médico de urgencias",
    organizacion="Clínica del Pacífico",
    ciudad="Cali",
)
