"""Laboratorio Bioandes: CSV separado por punto y coma.

Formato nativo: una fila por analito, con fecha-hora ISO, nombre del examen (la orden)
y rango de referencia.
"""

import csv
import io

CSV = """orden;doc_paciente;fecha_hora;examen;analito;valor;unidad;ref_min;ref_max
LB-2291;1032456789;2026-11-07T08:12;Hemograma y proteína C reactiva;Leucocitos;13.8;10^3/uL;4.5;11.0
LB-2291;1032456789;2026-11-07T08:12;Hemograma y proteína C reactiva;Hemoglobina;13.1;g/dL;12.0;16.0
LB-2291;1032456789;2026-11-07T08:12;Hemograma y proteína C reactiva;Plaquetas;310;10^3/uL;150;450
LB-2291;1032456789;2026-11-07T08:12;Hemograma y proteína C reactiva;Proteína C reactiva;48;mg/L;0;5
LB-2310;1017234567;2026-11-05T07:40;Perfil glucémico;Glucosa en ayunas;182;mg/dL;70;100
LB-2310;1017234567;2026-11-05T07:40;Perfil glucémico;Hemoglobina glicosilada;8.4;%;4.0;5.6
LB-2310;1017234567;2026-11-05T07:40;Perfil glucémico;Creatinina;0.9;mg/dL;0.7;1.3
LB-2345;1144056789;2026-10-28T09:15;Hemograma;Leucocitos;7.2;10^3/uL;4.5;11.0
LB-2345;1144056789;2026-10-28T09:15;Hemograma;Hemoglobina;15.1;g/dL;13.5;17.5
LB-2345;1144056789;2026-10-28T09:15;Hemograma;Plaquetas;250;10^3/uL;150;450
LB-2378;1000345678;2026-11-10T08:05;Hemograma;Leucocitos;6.8;10^3/uL;4.5;11.0
LB-2378;1000345678;2026-11-10T08:05;Hemograma;Hemoglobina;11.2;g/dL;12.0;16.0
LB-2378;1000345678;2026-11-10T08:05;Hemograma;Plaquetas;280;10^3/uL;150;450
LB-2402;19456321;2026-10-31T07:30;Función renal y electrolitos;Creatinina;1.4;mg/dL;0.7;1.3
LB-2402;19456321;2026-10-31T07:30;Función renal y electrolitos;Potasio;4.1;mmol/L;3.5;5.1
LB-2402;19456321;2026-10-31T07:30;Función renal y electrolitos;Sodio;138;mmol/L;135;145
LB-2403;19456321;2026-10-31T07:30;Gases arteriales;pH;7.33;;7.35;7.45
LB-2403;19456321;2026-10-31T07:30;Gases arteriales;PaCO2;52;mmHg;35;45
"""

def filas() -> list[dict]:
    """Parsea el CSV en una lista de diccionarios (una fila por analito)."""
    return list(csv.DictReader(io.StringIO(CSV), delimiter=";"))
