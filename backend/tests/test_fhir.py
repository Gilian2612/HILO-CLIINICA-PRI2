"""Paso 5b: constructores FHIR propios de Hilo Clínico: RDA, envío a la IPS y red de IPS."""

from datetime import datetime, timedelta, timezone

import pytest
from fhir.resources.R4B.bundle import Bundle

from app.consent import TODAS, consultar_red, crear_consentimiento
from app.fhir import ENDPOINT_IPS, RED_IPS, crear_envio_ips, crear_rda
from app.mpi import buscar

AHORA = datetime(2026, 11, 14, 22, 41, 7, tzinfo=timezone(timedelta(hours=-5)))
NOTA = "Antecedentes revisados en Hilo Clínico: alergia a la penicilina."


@pytest.fixture
def mariana():
    return buscar("1032456789").paciente


@pytest.fixture
def recursos(mariana):
    consent = crear_consentimiento(mariana, TODAS, "emergencia", AHORA)
    return consultar_red(mariana, consent, AHORA).recursos


def tipos(bundle):
    return [e.resource.get_resource_type() for e in bundle.entry]


# RDA: Bundle de tipo document


def test_rda_es_un_bundle_document_valido(mariana, recursos):
    rda = crear_rda(mariana, NOTA, AHORA, recursos)
    assert isinstance(rda, Bundle)
    assert rda.type == "document"
    assert rda.id == "rda-1032456789-202611142241"
    assert rda.timestamp == AHORA
    assert tipos(rda) == ["Composition", "Encounter", "AllergyIntolerance", "ClinicalImpression"]
    assert all(e.fullUrl for e in rda.entry)


def test_rda_composition_describe_la_atencion(mariana, recursos):
    composition = crear_rda(mariana, NOTA, AHORA, recursos).entry[0].resource
    assert composition.status == "final"
    assert composition.type.text == "Resumen Digital de Atención en Salud (RDA)"
    assert composition.title == "Atención de urgencias"
    assert composition.subject.reference == "Patient/hc-1032456789"
    assert composition.author[0].display == "Dr. Mateo Vargas, Clínica del Pacífico"


def test_rda_encounter_es_de_urgencias_y_la_impresion_lleva_la_nota(mariana, recursos):
    rda = crear_rda(mariana, NOTA, AHORA, recursos)
    encounter = rda.entry[1].resource
    assert encounter.status == "finished"
    assert encounter.class_fhir.code == "EMER"
    assert encounter.serviceProvider.display == "Clínica del Pacífico, Cali"
    impresion = rda.entry[3].resource
    assert impresion.status == "completed"
    assert impresion.summary == NOTA


def test_rda_sin_alergias_omite_esa_entrada(mariana):
    rda = crear_rda(mariana, NOTA, AHORA, [])
    assert tipos(rda) == ["Composition", "Encounter", "ClinicalImpression"]


# Envío a la IPS: Bundle de tipo transaction


def test_envio_es_un_bundle_transaction_con_post_por_entrada(mariana, recursos):
    rda = crear_rda(mariana, NOTA, AHORA, recursos)
    envio = crear_envio_ips(rda, AHORA)
    assert envio.type == "transaction"
    assert envio.id == "envio-20261114224107"
    assert tipos(envio) == ["Encounter", "ClinicalImpression", "Provenance"]
    assert all(e.request.method == "POST" for e in envio.entry)
    assert [e.request.url for e in envio.entry] == ["Encounter", "ClinicalImpression", "Provenance"]


def test_envio_enlaza_la_impresion_al_encounter_por_urn(mariana, recursos):
    envio = crear_envio_ips(crear_rda(mariana, NOTA, AHORA, recursos), AHORA)
    encounter, impresion, provenance = (e for e in envio.entry)
    assert encounter.fullUrl == "urn:uuid:enc-20261114224107"
    assert encounter.resource.identifier[0].value == "HC-20261114224107"
    assert impresion.resource.encounter.reference == encounter.fullUrl
    assert [t.reference for t in provenance.resource.target] == [encounter.fullUrl, impresion.fullUrl]
    assert provenance.resource.agent[0].who.display == "Hilo Clínico (capa de interoperabilidad)"


# Red de IPS


def test_la_red_tiene_endpoints_fhir_y_una_ips_que_atiende_hoy():
    assert ENDPOINT_IPS == "https://fhir.clinicadelpacifico.example/r4"
    assert len(RED_IPS) == 6
    hoy = next(i for i in RED_IPS if i.rol == "Atiende hoy")
    assert hoy.nombre == "Clínica del Pacífico"
    assert hoy.endpoint == "fhir.clinicadelpacifico.example/r4"
