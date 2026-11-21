"""Red de IPS conectadas: cada una expone un endpoint FHIR R4 (ficticio)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class IPSRed:
    nombre: str
    ciudad: str
    endpoint: str
    rol: str  # "Atiende hoy" | "Fuente de datos" | "Ejemplo"
    estado: str  # "ok" | "warn"


ENDPOINT_IPS = "https://fhir.clinicadelpacifico.example/r4"

RED_IPS: list[IPSRed] = [
    IPSRed("Clínica del Pacífico", "Cali", "fhir.clinicadelpacifico.example/r4", "Atiende hoy", "ok"),
    IPSRed("Centro Médico Chapinero", "Bogotá", "fhir.cmchapinero.example/r4", "Fuente de datos", "ok"),
    IPSRed("Fundación Santa Fe de Bogotá", "Bogotá", "fhir.fsfb.example/r4", "Ejemplo", "warn"),
    IPSRed("Fundación Clínica Cardioinfantil", "Bogotá", "fhir.cardioinfantil.example/r4", "Ejemplo", "warn"),
    IPSRed("Hospital Simón Bolívar", "Bogotá", "fhir.hsimonbolivar.example/r4", "Ejemplo", "warn"),
    IPSRed("Clínica de Marly", "Bogotá", "fhir.marly.example/r4", "Ejemplo", "warn"),
]


def endpoint_de(organizacion: str) -> str:
    """URL base FHIR de una IPS de la red (a donde se envía la atención)."""
    ips = next(i for i in RED_IPS if i.nombre == organizacion)
    return f"https://{ips.endpoint}"
