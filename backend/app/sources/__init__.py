"""Fuentes simuladas de la red, cada una en su formato nativo.

- EPS Andina: tabla plana (como un extracto de base de datos).
- Centro Médico Chapinero (IPS): JSON propio de su historia clínica.
- Laboratorio Bioandes: CSV separado por punto y coma.

Hilo Clínico no cambia estos formatos: los adaptadores (app.adapters) los traducen a FHIR.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Fuente:
    id: str
    tipo: str
    nombre: str
    ciudad: str
    formato: str
    color: str


FUENTES: dict[str, Fuente] = {
    "eps": Fuente("eps", "EPS", "EPS Andina", "Bogotá", "Tabla plana", "#C27A1E"),
    "ips": Fuente("ips", "IPS", "Centro Médico Chapinero", "Bogotá", "JSON propio", "#5B6FD6"),
    "lab": Fuente("lab", "Laboratorio", "Laboratorio Bioandes", "Bogotá", "CSV", "#1F9A7A"),
}
