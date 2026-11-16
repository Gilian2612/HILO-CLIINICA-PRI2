"""Paso 5c: la línea de tiempo que ve el médico se arma a partir de los recursos autorizados."""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.consent import TODAS, consultar_red, crear_consentimiento
from app.fhir import linea_de_tiempo
from app.mpi import buscar

AHORA = datetime(2026, 11, 14, 22, 41, 7, tzinfo=timezone(timedelta(hours=-5)))
HOY = date(2026, 11, 14)


@pytest.fixture
def mariana():
    return buscar("1032456789").paciente


@pytest.fixture
def todo(mariana):
    consent = crear_consentimiento(mariana, TODAS, "emergencia", AHORA)
    return consultar_red(mariana, consent, AHORA).recursos


def test_agrupa_los_recursos_en_items_ordenados_del_mas_reciente_al_mas_antiguo(todo):
    linea = linea_de_tiempo(todo, HOY)
    assert [i.tipo for i in linea.items] == ["laboratorio", "consulta", "autorizacion", "consulta", "formula"]
    assert [i.fuente for i in linea.items] == ["lab", "ips", "eps", "ips", "ips"]
    fechas = [i.fecha for i in linea.items]
    assert fechas == sorted(fechas, reverse=True)


def test_el_laboratorio_es_un_solo_item_con_todos_los_analitos(todo):
    lab = linea_de_tiempo(todo, HOY).items[0]
    assert lab.titulo == "Hemograma y proteína C reactiva"
    assert lab.fecha_label == "7 nov 2026"
    assert lab.hace == "hace 7 días"
    assert lab.reciente is True
    assert [a["nombre"] for a in lab.analitos] == ["Leucocitos", "Hemoglobina", "Plaquetas", "Proteína C reactiva"]
    assert lab.analitos[0]["bandera"] == "H"
    assert len(lab.recursos) == 4


def test_la_consulta_une_encounter_y_condition(todo):
    consulta = linea_de_tiempo(todo, HOY).items[1]
    assert consulta.titulo == "Consulta de medicina general"
    assert consulta.subtitulo == "R10.4 · Otros dolores abdominales y los no especificados"
    assert ("Profesional", "Dra. Laura Méndez") in consulta.detalle
    assert consulta.fecha_label == "6 nov 2026"
    assert len(consulta.recursos) == 2


def test_fechas_relativas():
    from app.fhir.linea_tiempo import hace

    assert hace(date(2026, 11, 14), HOY) == "hoy"
    assert hace(date(2026, 11, 7), HOY) == "hace 7 días"
    assert hace(date(2026, 8, 18), HOY) == "hace 3 meses"
    assert hace(date(2021, 2, 12), HOY) == "hace 5 años"


def test_alergias_y_cobertura_van_aparte(todo):
    linea = linea_de_tiempo(todo, HOY)
    assert len(linea.alergias) == 1
    assert linea.alergias[0].sustancia == "Penicilina"
    assert linea.alergias[0].critica is True
    assert linea.alergias[0].desde == "12 feb 2021"
    assert linea.cobertura.type.text == "Régimen contributivo"


def test_con_permiso_parcial_solo_aparece_lo_autorizado(mariana):
    consent = crear_consentimiento(mariana, ["laboratorios"], "paciente", AHORA)
    recursos = consultar_red(mariana, consent, AHORA).recursos
    linea = linea_de_tiempo(recursos, HOY)
    assert [i.tipo for i in linea.items] == ["laboratorio"]
    assert linea.alergias == []
    assert linea.cobertura is None
