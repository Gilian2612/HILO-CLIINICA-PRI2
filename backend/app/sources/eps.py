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
]

AUTORIZACIONES = [
    {
        "num_doc": "1032456789",
        "fecha": "20261106",
        "servicio": "Ecografía abdominal total",
        "estado": "APROBADA",
        "codigo": "AUT-88231",
    },
]


def afiliados() -> list[dict]:
    return [dict(a) for a in AFILIADOS]


def autorizaciones() -> list[dict]:
    return [dict(a) for a in AUTORIZACIONES]
