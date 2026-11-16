"""Paso 3: cada adaptador traduce su fuente nativa a recursos FHIR R4 válidos."""

import pytest
from fhir.resources.R4B.resource import Resource

from app.adapters import ADAPTADORES, eps, ips, lab
from app.mpi import buscar


@pytest.fixture
def mariana():
    return buscar("1032456789").paciente


@pytest.fixture
def jorge():
    return buscar("79845120").paciente


def tipos(recursos):
    return [r.get_resource_type() for r in recursos]


def referencia_paciente(recurso):
    """Cada tipo FHIR guarda la referencia al paciente en un campo distinto."""
    campo = getattr(recurso, "beneficiary", None) or getattr(recurso, "patient", None)
    return (campo or recurso.subject).reference


def test_hay_un_adaptador_por_fuente_y_declara_sus_tipos():
    assert set(ADAPTADORES) == {"eps", "ips", "lab"}
    assert ADAPTADORES["eps"].tipos == ("Coverage", "ServiceRequest")
    assert ADAPTADORES["ips"].tipos == (
        "AllergyIntolerance",
        "Encounter",
        "Condition",
        "MedicationRequest",
    )
    assert ADAPTADORES["lab"].tipos == ("Observation",)


def test_todos_los_recursos_son_fhir_validos(mariana):
    for adaptador in ADAPTADORES.values():
        for recurso in adaptador.a_fhir(mariana):
            assert isinstance(recurso, Resource)
            assert referencia_paciente(recurso) == f"Patient/{mariana.id}"


# EPS: tabla plana → Coverage + ServiceRequest


def test_eps_traduce_afiliacion_a_coverage(mariana):
    cobertura = eps.a_fhir(mariana)[0]
    assert cobertura.get_resource_type() == "Coverage"
    assert cobertura.id == "cov-1032456789"
    assert cobertura.status == "active"
    assert cobertura.type.text == "Régimen contributivo"
    assert cobertura.payor[0].display == "EPS Andina"


def test_eps_traduce_autorizacion_a_servicerequest(mariana):
    autorizacion = eps.a_fhir(mariana)[1]
    assert autorizacion.get_resource_type() == "ServiceRequest"
    assert autorizacion.id == "AUT-88231"
    assert autorizacion.status == "active"
    assert autorizacion.intent == "order"
    assert autorizacion.code.text == "Ecografía abdominal total"
    assert str(autorizacion.authoredOn) == "2026-11-06"
    assert autorizacion.insurance[0].reference == "Coverage/cov-1032456789"


def test_eps_regimen_subsidiado_sin_autorizaciones(jorge):
    recursos = eps.a_fhir(jorge)
    assert tipos(recursos) == ["Coverage"]
    assert recursos[0].type.text == "Régimen subsidiado"


# IPS: JSON propio → AllergyIntolerance + Encounter + Condition + MedicationRequest


def test_ips_traduce_alergia_con_criticidad_alta(mariana):
    alergia = next(r for r in ips.a_fhir(mariana) if r.get_resource_type() == "AllergyIntolerance")
    assert alergia.id == "alg-P-00417-1"
    assert alergia.code.text == "Penicilina"
    assert alergia.criticality == "high"
    assert alergia.reaction[0].severity == "severe"
    assert alergia.reaction[0].manifestation[0].text.startswith("Urticaria")
    assert str(alergia.recordedDate) == "2021-02-12"


def test_ips_traduce_cada_atencion_en_encounter_mas_condition(mariana):
    recursos = ips.a_fhir(mariana)
    encuentros = [r for r in recursos if r.get_resource_type() == "Encounter"]
    condiciones = [r for r in recursos if r.get_resource_type() == "Condition"]
    assert len(encuentros) == 2
    assert len(condiciones) == 2
    assert encuentros[1].id == "enc-P-00417-2"
    assert encuentros[1].class_fhir.code == "AMB"
    assert str(encuentros[1].period.start) == "2026-11-06"
    assert encuentros[1].reasonCode[0].text == "Dolor abdominal de dos días"
    assert condiciones[1].encounter.reference == "Encounter/enc-P-00417-2"
    assert condiciones[1].code.coding[0].system == "http://hl7.org/fhir/sid/icd-10"
    assert condiciones[1].code.coding[0].code == "R10.4"
    assert condiciones[1].note[0].text.startswith("Se ordenan hemograma")
    assert condiciones[0].note is None


def test_ips_traduce_formula_a_medicationrequest(mariana):
    formula = next(r for r in ips.a_fhir(mariana) if r.get_resource_type() == "MedicationRequest")
    assert formula.id == "med-P-00417-1"
    assert formula.medicationCodeableConcept.text == "Salbutamol inhalador 100 mcg"
    assert formula.dosageInstruction[0].text == "2 inhalaciones cada 6 horas si hay síntomas"


def test_ips_no_conoce_a_jorge(jorge):
    assert ips.a_fhir(jorge) == []


# Laboratorio: CSV → Observation


def test_lab_traduce_cada_fila_a_observation_de_laboratorio(mariana):
    observaciones = lab.a_fhir(mariana)
    assert tipos(observaciones) == ["Observation"] * 4
    leucocitos = observaciones[0]
    assert leucocitos.id == "obs-LB-2291-1"
    assert leucocitos.status == "final"
    assert leucocitos.category[0].coding[0].code == "laboratory"
    assert leucocitos.code.text == "Leucocitos"
    assert leucocitos.effectiveDateTime.isoformat() == "2026-11-07T08:12:00-05:00"
    assert float(leucocitos.valueQuantity.value) == 13.8
    assert leucocitos.valueQuantity.unit == "10^3/uL"
    assert leucocitos.performer[0].display == "Laboratorio Bioandes"
    assert leucocitos.identifier[0].value == "LB-2291"


def test_lab_interpreta_el_valor_contra_el_rango_de_referencia(mariana):
    por_analito = {o.code.text: o for o in lab.a_fhir(mariana)}
    assert por_analito["Leucocitos"].interpretation[0].coding[0].code == "H"
    assert por_analito["Leucocitos"].interpretation[0].text == "Alto"
    assert por_analito["Hemoglobina"].interpretation[0].coding[0].code == "N"
    assert por_analito["Proteína C reactiva"].interpretation[0].coding[0].code == "H"


def test_lab_no_conoce_a_jorge(jorge):
    assert lab.a_fhir(jorge) == []


def test_fecha_hora_local_se_completa_al_formato_fhir():
    from app.adapters._comun import de_fecha_hora_local

    assert de_fecha_hora_local("2026-11-07T08:12") == "2026-11-07T08:12:00-05:00"
    assert de_fecha_hora_local("2026-11-07T08:12:30") == "2026-11-07T08:12:30-05:00"
    assert de_fecha_hora_local("2026-11-07T13:12:00Z") == "2026-11-07T13:12:00Z"
    assert de_fecha_hora_local("2026-11-07T08:12:00-05:00") == "2026-11-07T08:12:00-05:00"
