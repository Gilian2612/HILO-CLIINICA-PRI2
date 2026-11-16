"""Centro Médico Chapinero (IPS): JSON propio de su historia clínica.

Formato nativo: IDs internos (P-00417), documento con puntos (CC-1.032.456.789),
fechas en DD/MM/AAAA, nombre como 'Apellidos, Nombres'.
"""

import copy

DATOS = {
    "pacientes": [
        {
            "id": "P-00417",
            "documento": "CC-1.032.456.789",
            "nombre": "López Castro, Mariana Sofía",
            "nacimiento": "14/03/1992",
            "sexo": "F",
        },
    ],
    "alergias": [
        {
            "pid": "P-00417",
            "sustancia": "Penicilina",
            "reaccion": "Urticaria generalizada y dificultad para respirar",
            "gravedad": "ALTA",
            "registrada": "12/02/2021",
        },
    ],
    "atenciones": [
        {
            "pid": "P-00417",
            "fecha": "18/08/2026",
            "tipo": "Consulta de medicina general",
            "motivo": "Control de asma",
            "cie10": "J45.9",
            "dx": "Asma, no especificada",
            "profesional": "Dra. Laura Méndez",
        },
        {
            "pid": "P-00417",
            "fecha": "06/11/2026",
            "tipo": "Consulta de medicina general",
            "motivo": "Dolor abdominal de dos días",
            "cie10": "R10.4",
            "dx": "Otros dolores abdominales y los no especificados",
            "profesional": "Dra. Laura Méndez",
            "plan": "Se ordenan hemograma, proteína C reactiva y ecografía abdominal.",
        },
    ],
    "formulas": [
        {
            "pid": "P-00417",
            "fecha": "18/08/2026",
            "medicamento": "Salbutamol inhalador 100 mcg",
            "dosis": "2 inhalaciones cada 6 horas si hay síntomas",
        },
    ],
}


def datos() -> dict:
    return copy.deepcopy(DATOS)
