"""Paso 1: las fuentes de la red entregan sus datos en su formato nativo."""

from app.sources import FUENTES, eps, ips, lab


def test_hay_tres_fuentes_con_su_formato():
    assert set(FUENTES) == {"eps", "ips", "lab"}
    assert FUENTES["eps"].formato == "Tabla plana"
    assert FUENTES["ips"].formato == "JSON propio"
    assert FUENTES["lab"].formato == "CSV"


def test_eps_entrega_tabla_plana_con_fechas_aaaammdd():
    afiliados = eps.afiliados()
    mariana = next(a for a in afiliados if a["num_doc"] == "1032456789")
    assert mariana["fec_nac"] == "19920314"
    assert mariana["regimen"] == "C"
    assert mariana["estado"] == "AC"


def test_eps_tiene_una_autorizacion_aprobada_para_mariana():
    autorizaciones = [a for a in eps.autorizaciones() if a["num_doc"] == "1032456789"]
    assert len(autorizaciones) == 1
    assert autorizaciones[0]["estado"] == "APROBADA"
    assert autorizaciones[0]["codigo"] == "AUT-88231"


def test_ips_entrega_json_propio_con_ids_locales_y_fechas_ddmmaaaa():
    datos = ips.datos()
    paciente = datos["pacientes"][0]
    assert paciente["id"] == "P-00417"
    assert paciente["documento"] == "CC-1.032.456.789"
    assert paciente["nacimiento"] == "14/03/1992"
    assert len(datos["alergias"]) == 1
    assert len(datos["atenciones"]) == 2
    assert len(datos["formulas"]) == 1


def test_lab_entrega_csv_separado_por_punto_y_coma():
    assert lab.CSV.splitlines()[0] == (
        "orden;doc_paciente;fecha_hora;analito;valor;unidad;ref_min;ref_max"
    )


def test_lab_parsea_el_csv_en_filas():
    filas = lab.filas()
    assert len(filas) == 4
    assert filas[0]["orden"] == "LB-2291"
    assert filas[0]["analito"] == "Leucocitos"
    assert filas[0]["valor"] == "13.8"
    assert filas[3]["analito"] == "Proteína C reactiva"
