"""EPS Andina: tabla plana.

Formato nativo: filas con columnas cortas, fechas en AAAAMMDD, códigos de una letra
(regimen C = contributivo, S = subsidiado; estado AC = activo).
"""

AFILIADOS = [
    {
        "tipo_doc": "CC",
        "num_doc": "1032456789",
        "nombres": "MARIANA SOFIA",
        "apellidos": "LOPEZ CASTRO",
        "fec_nac": "19920314",
        "sexo": "F",
        "regimen": "C",
        "estado": "AC",
    },
    {
        "tipo_doc": "CC",
        "num_doc": "79845120",
        "nombres": "JORGE ELIECER",
        "apellidos": "PARDO RUIZ",
        "fec_nac": "19710902",
        "sexo": "M",
        "regimen": "S",
        "estado": "AC",
    },
    {
        "tipo_doc": "CC",
        "num_doc": "1017234567",
        "nombres": "CARLOS ANDRES",
        "apellidos": "GOMEZ RESTREPO",
        "fec_nac": "19880522",
        "sexo": "M",
        "regimen": "C",
        "estado": "AC",
    },
    {
        "tipo_doc": "CC",
        "num_doc": "52987654",
        "nombres": "LUISA FERNANDA",
        "apellidos": "ROJAS HERRERA",
        "fec_nac": "19791103",
        "sexo": "F",
        "regimen": "C",
        "estado": "AC",
    },
    {
        "tipo_doc": "CC",
        "num_doc": "1144056789",
        "nombres": "ANDRES FELIPE",
        "apellidos": "MARTINEZ OSPINA",
        "fec_nac": "19950715",
        "sexo": "M",
        "regimen": "S",
        "estado": "AC",
    },
    {
        "tipo_doc": "CC",
        "num_doc": "1000345678",
        "nombres": "VALENTINA",
        "apellidos": "RUIZ QUINTERO",
        "fec_nac": "20010130",
        "sexo": "F",
        "regimen": "C",
        "estado": "AC",
    },
    {
        "tipo_doc": "CC",
        "num_doc": "19456321",
        "nombres": "HECTOR JULIO",
        "apellidos": "CARDENAS PINZON",
        "fec_nac": "19580912",
        "sexo": "M",
        "regimen": "S",
        "estado": "AC",
    },
]

AUTORIZACIONES = [
    {
        "num_doc": "1032456789",
        "fecha": "20261106",
        "servicio": "Ecografía abdominal total",
        "estado": "APROBADA",
        "codigo": "AUT-88231",
    },
    {
        "num_doc": "52987654",
        "fecha": "20261020",
        "servicio": "Ecocardiograma transtorácico",
        "estado": "APROBADA",
        "codigo": "AUT-88412",
    },
    {
        "num_doc": "1144056789",
        "fecha": "20261029",
        "servicio": "Resonancia magnética de rodilla derecha",
        "estado": "APROBADA",
        "codigo": "AUT-88507",
    },
]


def afiliados() -> list[dict]:
    return [dict(a) for a in AFILIADOS]


def autorizaciones() -> list[dict]:
    return [dict(a) for a in AUTORIZACIONES]
