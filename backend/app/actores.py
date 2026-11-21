"""Actores de la simulación: médicos de urgencias de las clínicas de la red (datos ficticios).

Cada médico trabaja en una IPS distinta de `app.fhir.red.RED_IPS`. El médico que atiende
se elige al crear la simulación; si no se elige, atiende el Dr. Mateo Vargas (el del boceto).
"""

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

MEDICOS: dict[str, Profesional] = {
    m.id: m
    for m in [
        MEDICO,
        Profesional("prac-0347", "Dra. Catalina Ríos", "Médica de urgencias",
                    "Fundación Santa Fe de Bogotá", "Bogotá"),
        Profesional("prac-0418", "Dr. Julián Ortega", "Médico de urgencias",
                    "Centro Médico Chapinero", "Bogotá"),
        Profesional("prac-0523", "Dra. Paula Cifuentes", "Médica de urgencias",
                    "Fundación Clínica Cardioinfantil", "Bogotá"),
        Profesional("prac-0611", "Dr. Sebastián Mejía", "Médico de urgencias",
                    "Hospital Simón Bolívar", "Bogotá"),
        Profesional("prac-0735", "Dra. Natalia Herrera", "Médica de urgencias",
                    "Clínica de Marly", "Bogotá"),
    ]
}


def medico_por_id(id: str) -> Profesional | None:
    return MEDICOS.get(id)
