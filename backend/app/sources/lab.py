"""Laboratorio Bioandes: CSV separado por punto y coma.

Formato nativo: una fila por analito, con fecha-hora ISO y rango de referencia.
"""

import csv
import io

CSV = """orden;doc_paciente;fecha_hora;analito;valor;unidad;ref_min;ref_max
LB-2291;1032456789;2026-11-07T08:12;Leucocitos;13.8;10^3/uL;4.5;11.0
LB-2291;1032456789;2026-11-07T08:12;Hemoglobina;13.1;g/dL;12.0;16.0
LB-2291;1032456789;2026-11-07T08:12;Plaquetas;310;10^3/uL;150;450
LB-2291;1032456789;2026-11-07T08:12;Proteína C reactiva;48;mg/L;0;5
"""


def filas() -> list[dict]:
    """Parsea el CSV en una lista de diccionarios (una fila por analito)."""
    return list(csv.DictReader(io.StringIO(CSV), delimiter=";"))
