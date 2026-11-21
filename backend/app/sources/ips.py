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
        {
            "id": "P-00532",
            "documento": "CC-1.017.234.567",
            "nombre": "Gómez Restrepo, Carlos Andrés",
            "nacimiento": "22/05/1988",
            "sexo": "M",
        },
        {
            "id": "P-00588",
            "documento": "CC-52.987.654",
            "nombre": "Rojas Herrera, Luisa Fernanda",
            "nacimiento": "03/11/1979",
            "sexo": "F",
        },
        {
            "id": "P-00641",
            "documento": "CC-1.000.345.678",
            "nombre": "Ruiz Quintero, Valentina",
            "nacimiento": "30/01/2001",
            "sexo": "F",
        },
        {
            "id": "P-00702",
            "documento": "CC-19.456.321",
            "nombre": "Cárdenas Pinzón, Héctor Julio",
            "nacimiento": "12/09/1958",
            "sexo": "M",
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
        {
            "pid": "P-00532",
            "sustancia": "Sulfonamidas",
            "reaccion": "Erupción cutánea pruriginosa",
            "gravedad": "MEDIA",
            "registrada": "03/06/2019",
        },
        {
            "pid": "P-00588",
            "sustancia": "Ibuprofeno y otros AINE",
            "reaccion": "Angioedema facial",
            "gravedad": "ALTA",
            "registrada": "20/04/2018",
        },
        {
            "pid": "P-00641",
            "sustancia": "Látex",
            "reaccion": "Dermatitis de contacto",
            "gravedad": "MEDIA",
            "registrada": "11/08/2023",
        },
        {
            "pid": "P-00702",
            "sustancia": "Ácido acetilsalicílico (aspirina)",
            "reaccion": "Broncoespasmo",
            "gravedad": "ALTA",
            "registrada": "14/01/2015",
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
        {
            "pid": "P-00532",
            "fecha": "15/09/2026",
            "tipo": "Consulta de medicina interna",
            "motivo": "Control de diabetes",
            "cie10": "E11.9",
            "dx": "Diabetes mellitus tipo 2 sin complicaciones",
            "profesional": "Dr. Ricardo Peña",
            "plan": "Se ajusta la metformina. Hemoglobina glicosilada de control en noviembre.",
        },
        {
            "pid": "P-00588",
            "fecha": "02/10/2026",
            "tipo": "Consulta de medicina general",
            "motivo": "Control de hipertensión",
            "cie10": "I10",
            "dx": "Hipertensión esencial (primaria)",
            "profesional": "Dra. Laura Méndez",
            "plan": "Se solicita ecocardiograma transtorácico.",
        },
        {
            "pid": "P-00641",
            "fecha": "25/07/2026",
            "tipo": "Consulta de medicina general",
            "motivo": "Cefalea recurrente",
            "cie10": "G43.9",
            "dx": "Migraña, no especificada",
            "profesional": "Dra. Laura Méndez",
        },
        {
            "pid": "P-00702",
            "fecha": "03/03/2026",
            "tipo": "Consulta de neumología",
            "motivo": "Control de EPOC",
            "cie10": "J44.9",
            "dx": "Enfermedad pulmonar obstructiva crónica, no especificada",
            "profesional": "Dr. Hernán Castillo",
        },
        {
            "pid": "P-00702",
            "fecha": "30/10/2026",
            "tipo": "Consulta de medicina general",
            "motivo": "Aumento de la disnea",
            "cie10": "J44.1",
            "dx": "EPOC con exacerbación aguda, no especificada",
            "profesional": "Dr. Hernán Castillo",
            "plan": "Se ordenan gases arteriales y función renal.",
        },
    ],
    "formulas": [
        {
            "pid": "P-00417",
            "fecha": "18/08/2026",
            "medicamento": "Salbutamol inhalador 100 mcg",
            "dosis": "2 inhalaciones cada 6 horas si hay síntomas",
        },
        {
            "pid": "P-00532",
            "fecha": "15/09/2026",
            "medicamento": "Metformina 850 mg",
            "dosis": "1 tableta cada 12 horas con las comidas",
        },
        {
            "pid": "P-00588",
            "fecha": "02/10/2026",
            "medicamento": "Losartán 50 mg",
            "dosis": "1 tableta cada 12 horas",
        },
        {
            "pid": "P-00641",
            "fecha": "25/07/2026",
            "medicamento": "Acetaminofén 500 mg",
            "dosis": "2 tabletas cada 8 horas si hay dolor",
        },
        {
            "pid": "P-00702",
            "fecha": "03/03/2026",
            "medicamento": "Tiotropio inhalador 2,5 mcg",
            "dosis": "2 inhalaciones una vez al día",
        },
    ],
}


def datos() -> dict:
    return copy.deepcopy(DATOS)
