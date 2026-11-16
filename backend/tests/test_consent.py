"""Paso 4: el gestor de consentimiento decide qué se puede consultar y por cuánto tiempo."""

from datetime import datetime, timedelta, timezone

import pytest
from fhir.resources.R4B.consent import Consent

from app.consent import (
    CATEGORIAS,
    TODAS,
    consultar_red,
    crear_consentimiento,
    permite,
    revocar,
    tipos_de,
)
from app.mpi import buscar

AHORA = datetime(2026, 11, 14, 22, 41, 7, tzinfo=timezone(timedelta(hours=-5)))


@pytest.fixture
def mariana():
    return buscar("1032456789").paciente


# Categorías


def test_hay_cuatro_categorias_que_la_paciente_puede_autorizar():
    assert [c.id for c in CATEGORIAS] == ["alergias", "laboratorios", "consultas", "eps"]
    assert TODAS == ["alergias", "laboratorios", "consultas", "eps"]


def test_cada_categoria_habilita_tipos_de_recurso():
    assert tipos_de(["alergias"]) == ["AllergyIntolerance", "MedicationRequest"]
    assert tipos_de(["laboratorios", "eps"]) == ["Observation", "Coverage", "ServiceRequest"]
    assert tipos_de([]) == []


# Creación del Consent


def test_consentimiento_de_la_paciente_es_un_consent_fhir_valido(mariana):
    consent = crear_consentimiento(mariana, ["alergias", "laboratorios"], "paciente", AHORA)
    assert isinstance(consent, Consent)
    assert consent.id == "consent-1032456789-paciente"
    assert consent.status == "active"
    assert consent.scope.text == "Autorización de la paciente"
    assert consent.patient.reference == "Patient/hc-1032456789"
    assert consent.performer[0].display == mariana.nombre
    assert consent.provision.type == "permit"


def test_consentimiento_vence_a_las_24_horas(mariana):
    consent = crear_consentimiento(mariana, TODAS, "paciente", AHORA)
    assert consent.provision.period.start == AHORA
    assert consent.provision.period.end == AHORA + timedelta(hours=24)


def test_consentimiento_lista_los_tipos_autorizados(mariana):
    consent = crear_consentimiento(mariana, ["consultas"], "paciente", AHORA)
    assert [c.code for c in consent.provision.class_fhir] == ["Encounter", "Condition"]


def test_consentimiento_autoriza_al_medico_y_su_ips(mariana):
    consent = crear_consentimiento(mariana, TODAS, "paciente", AHORA)
    assert consent.provision.actor[0].reference.display == "Dr. Mateo Vargas, Clínica del Pacífico"


def test_acceso_de_emergencia_lo_abre_el_medico_y_cubre_todo(mariana):
    consent = crear_consentimiento(mariana, TODAS, "emergencia", AHORA)
    assert consent.id == "consent-1032456789-emergencia"
    assert consent.scope.text == "Acceso de emergencia (urgencia vital)"
    assert consent.performer[0].display == "Dr. Mateo Vargas"
    assert len(consent.provision.class_fhir) == 7


# Regla central: sin permiso no se consulta


def test_permite_solo_los_tipos_autorizados(mariana):
    consent = crear_consentimiento(mariana, ["alergias"], "paciente", AHORA)
    assert permite(consent, "AllergyIntolerance", AHORA)
    assert permite(consent, "MedicationRequest", AHORA)
    assert not permite(consent, "Observation", AHORA)
    assert not permite(consent, "Coverage", AHORA)


def test_sin_consentimiento_no_se_permite_nada():
    assert not permite(None, "AllergyIntolerance", AHORA)


def test_el_permiso_caduca_despues_de_24_horas(mariana):
    consent = crear_consentimiento(mariana, TODAS, "paciente", AHORA)
    assert permite(consent, "Observation", AHORA + timedelta(hours=23, minutes=59))
    assert not permite(consent, "Observation", AHORA + timedelta(hours=24, seconds=1))


def test_revocar_deja_el_consent_inactivo_y_bloquea_todo(mariana):
    consent = crear_consentimiento(mariana, TODAS, "paciente", AHORA)
    revocado = revocar(consent)
    assert revocado.status == "inactive"
    assert not permite(revocado, "Observation", AHORA)
    assert consent.status == "active"  # el original no se modifica


# Consulta a la red respetando el consentimiento


def test_consultar_red_trae_solo_lo_autorizado_y_registra_403_en_lo_demas(mariana):
    consent = crear_consentimiento(mariana, ["alergias", "laboratorios"], "paciente", AHORA)
    resultado = consultar_red(mariana, consent, AHORA)

    tipos_traidos = {r.get_resource_type() for r in resultado.recursos}
    assert tipos_traidos == {"AllergyIntolerance", "MedicationRequest", "Observation"}

    por_tipo = {p.tipo: p for p in resultado.log}
    assert por_tipo["Observation"].status == 200
    assert por_tipo["Observation"].cantidad == 4
    assert por_tipo["Observation"].url == "/Observation?patient=hc-1032456789&category=laboratory"
    assert por_tipo["Coverage"].status == 403
    assert por_tipo["Coverage"].cantidad == 0
    assert por_tipo["Coverage"].url == "/Coverage?beneficiary=hc-1032456789"
    assert por_tipo["Encounter"].status == 403


def test_consultar_red_sin_consentimiento_no_trae_nada(mariana):
    resultado = consultar_red(mariana, None, AHORA)
    assert resultado.recursos == []
    assert all(p.status == 403 for p in resultado.log)
    assert len(resultado.log) == 7


def test_consultar_red_con_todo_autorizado_trae_los_doce_recursos(mariana):
    consent = crear_consentimiento(mariana, TODAS, "emergencia", AHORA)
    resultado = consultar_red(mariana, consent, AHORA)
    # 1 Coverage + 1 ServiceRequest + 1 alergia + 2 Encounter + 2 Condition + 1 fórmula + 4 Observation
    assert len(resultado.recursos) == 12
    assert all(p.status == 200 for p in resultado.log)
    assert {p.fuente for p in resultado.log} == {"eps", "ips", "lab"}
