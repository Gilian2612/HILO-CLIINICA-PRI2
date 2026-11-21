"""Paso 9: cinco casos de ejemplo más, con médicos de varias clínicas de la red.

Cada caso es un paciente (CC y nombre) que llega a urgencias de una clínica de la red y
lo atiende un médico de esa clínica. El médico se elige al crear la simulación.
"""

from datetime import datetime, timedelta, timezone

import unicodedata

import pytest
from fastapi.testclient import TestClient

from app.actores import MEDICO, MEDICOS, medico_por_id
from app.adapters import ADAPTADORES
from app.casos import CASOS, caso_de
from app.consent import TODAS, crear_consentimiento
from app.fhir import RED_IPS, crear_rda, endpoint_de, linea_de_tiempo
from app.main import app
from app.mpi import buscar
from app.process import correr, nueva_simulacion
from app.process.motor import NOTA_POR_DEFECTO, actuar

AHORA = datetime(2026, 11, 14, 22, 41, 7, tzinfo=timezone(timedelta(hours=-5)))
INICIO = "2026-11-14T22:41:07-05:00"

NUEVOS = ["1017234567", "52987654", "1144056789", "1000345678", "19456321"]


def sin_tildes(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def recursos_de(documento: str) -> list:
    paciente = buscar(documento).paciente
    return [r for a in ADAPTADORES.values() for r in a.a_fhir(paciente)]


# Catálogo de médicos y casos


def test_hay_seis_medicos_cada_uno_en_una_clinica_distinta_de_la_red():
    assert len(MEDICOS) == 6
    clinicas_red = {i.nombre for i in RED_IPS}
    organizaciones = [m.organizacion for m in MEDICOS.values()]
    assert len(set(organizaciones)) == 6
    assert set(organizaciones) <= clinicas_red


def test_el_medico_por_defecto_sigue_siendo_mateo_vargas():
    assert MEDICO.id == "prac-0192"
    assert medico_por_id("prac-0192") is MEDICO
    assert medico_por_id("no-existe") is None


def test_cada_medico_tiene_el_endpoint_fhir_de_su_clinica():
    assert endpoint_de("Clínica del Pacífico") == "https://fhir.clinicadelpacifico.example/r4"
    for medico in MEDICOS.values():
        assert endpoint_de(medico.organizacion).startswith("https://fhir.")


def test_hay_siete_casos_mariana_jorge_y_cinco_nuevos():
    assert [c.documento for c in CASOS] == ["1032456789", "79845120", *NUEVOS]
    for caso in CASOS:
        assert caso.medico in MEDICOS
        assert caso.motivo and caso.nota


def test_caso_de_busca_por_documento_normalizado():
    assert caso_de("CC 1.017.234.567").nombre == "Carlos Andrés Gómez Restrepo"
    assert caso_de("123") is None


# Los cinco pacientes nuevos en la red


@pytest.mark.parametrize("documento", NUEVOS)
def test_cada_paciente_nuevo_se_encuentra_en_el_mpi(documento):
    resultado = buscar(documento)
    assert resultado.paciente.id == f"hc-{documento}"
    # Andrés solo está en la EPS, que guarda los nombres sin tildes.
    assert sin_tildes(resultado.paciente.nombre) == sin_tildes(caso_de(documento).nombre)


@pytest.mark.parametrize(
    "documento, fuentes",
    [
        ("1017234567", {"eps", "ips", "lab"}),
        ("52987654", {"eps", "ips"}),
        ("1144056789", {"eps", "lab"}),
        ("1000345678", {"eps", "ips", "lab"}),
        ("19456321", {"eps", "ips", "lab"}),
    ],
)
def test_cada_paciente_esta_en_las_fuentes_esperadas(documento, fuentes):
    assert {i.fuente for i in buscar(documento).identidades} == fuentes


@pytest.mark.parametrize("documento", NUEVOS)
def test_los_recursos_de_cada_paciente_apuntan_al_paciente_maestro(documento):
    recursos = recursos_de(documento)
    assert recursos
    for r in recursos:
        sujeto = getattr(r, "subject", None) or getattr(r, "patient", None) or r.beneficiary
        assert sujeto.reference == f"Patient/hc-{documento}"


def test_luisa_tiene_alergia_grave_a_los_aines():
    alergias = [r for r in recursos_de("52987654") if r.get_resource_type() == "AllergyIntolerance"]
    assert [a.code.text for a in alergias] == ["Ibuprofeno y otros AINE"]
    assert alergias[0].criticality == "high"


def test_cada_orden_de_laboratorio_es_un_item_con_el_nombre_del_examen():
    linea = linea_de_tiempo(recursos_de("19456321"), AHORA.date())
    labs = [i for i in linea.items if i.tipo == "laboratorio"]
    assert [i.titulo for i in labs] == ["Función renal y electrolitos", "Gases arteriales"]


def test_mariana_conserva_su_examen():
    linea = linea_de_tiempo(recursos_de("1032456789"), AHORA.date())
    labs = [i for i in linea.items if i.tipo == "laboratorio"]
    assert [i.titulo for i in labs] == ["Hemograma y proteína C reactiva"]


# El médico elegido aparece en el Consent, el RDA y el envío


def test_el_consent_nombra_al_medico_elegido():
    medico = MEDICOS["prac-0347"]
    paciente = buscar("1017234567").paciente
    consent = crear_consentimiento(paciente, TODAS, "emergencia", AHORA, medico=medico)
    assert consent.provision.actor[0].reference.display == medico.display
    assert consent.performer[0].display == medico.nombre


def test_el_rda_lleva_al_medico_su_clinica_y_el_motivo():
    medico = MEDICOS["prac-0347"]
    paciente = buscar("1017234567").paciente
    rda = crear_rda(paciente, "nota", AHORA, [], medico=medico, motivo="Hiperglucemia")
    composicion, encuentro = rda.entry[0].resource, rda.entry[1].resource
    assert composicion.author[0].display == medico.display
    assert encuentro.serviceProvider.display == f"{medico.organizacion}, {medico.ciudad}"
    assert encuentro.reasonCode[0].text == "Hiperglucemia"


# La simulación con otro médico


def test_la_simulacion_guarda_el_medico_elegido():
    sim = nueva_simulacion("consentimiento", AHORA, medico="prac-0347")
    assert sim.medico.nombre == MEDICOS["prac-0347"].nombre
    assert nueva_simulacion("consentimiento", AHORA).medico is MEDICO


def test_la_simulacion_rechaza_un_medico_desconocido():
    with pytest.raises(ValueError):
        nueva_simulacion("consentimiento", AHORA, medico="no-existe")


def test_al_encontrar_al_paciente_la_nota_por_defecto_se_cambia_por_la_del_caso():
    sim = nueva_simulacion("consentimiento", AHORA, medico="prac-0347")
    actuar(sim, documento="1017234567")
    assert sim.ctx.borrador.nota == caso_de("1017234567").nota


def test_si_el_medico_ya_escribio_la_nota_no_se_toca():
    sim = nueva_simulacion("consentimiento", AHORA)
    sim.ctx.borrador.nota = "Mi nota"
    actuar(sim, documento="1017234567")
    assert sim.ctx.borrador.nota == "Mi nota"


def test_mariana_conserva_la_nota_del_boceto():
    sim = nueva_simulacion("consentimiento", AHORA)
    actuar(sim, documento="1032456789")
    assert sim.ctx.borrador.nota == NOTA_POR_DEFECTO


def test_la_auditoria_y_el_envio_usan_al_medico_y_su_clinica():
    sim = nueva_simulacion("consentimiento", AHORA, medico="prac-0347")
    sim.ctx.borrador.documento = "1017234567"
    sim.ctx.borrador.destino = "ips"
    sim = correr(sim)
    medico = MEDICOS["prac-0347"]
    quienes = {e.quien for e in sim.ctx.auditoria}
    assert medico.nombre in quienes and MEDICO.nombre not in quienes
    assert sim.ctx.log[-1].url == endpoint_de(medico.organizacion)
    assert sim.ctx.rda.entry[1].resource.reasonCode[0].text == caso_de("1017234567").motivo


# API


@pytest.fixture
def client():
    return TestClient(app)


def test_catalogo_incluye_medicos_y_casos(client):
    datos = client.get("/api/catalogo").json()
    assert len(datos["medicos"]) == 6
    assert datos["medicos"][0]["id"] == "prac-0192"
    assert all("endpoint" in m and "display" in m for m in datos["medicos"])
    assert [c["documento"] for c in datos["casos"]][2:] == NUEVOS


def test_crear_simulacion_con_medico(client):
    r = client.post(
        "/api/simulaciones", json={"escenario": "consentimiento", "inicio": INICIO, "medico": "prac-0347"}
    )
    assert r.status_code == 201
    assert r.json()["medico"]["id"] == "prac-0347"
    assert r.json()["medico"]["endpoint"].startswith("https://")


def test_crear_simulacion_sin_medico_usa_el_de_turno(client):
    r = client.post("/api/simulaciones", json={"escenario": "consentimiento", "inicio": INICIO})
    assert r.json()["medico"]["id"] == "prac-0192"


def test_crear_simulacion_con_medico_desconocido_responde_422(client):
    r = client.post("/api/simulaciones", json={"escenario": "consentimiento", "medico": "nadie"})
    assert r.status_code == 422


def test_la_simulacion_arranca_con_la_cedula_del_caso_del_medico():
    assert nueva_simulacion("consentimiento", AHORA, medico="prac-0418").ctx.borrador.documento == "52987654"
    assert nueva_simulacion("consentimiento", AHORA).ctx.borrador.documento == "1032456789"
