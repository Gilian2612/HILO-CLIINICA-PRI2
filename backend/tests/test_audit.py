"""Paso 5a: cada paso del proceso deja un evento de auditoría que se proyecta a AuditEvent FHIR."""

from datetime import datetime, timedelta, timezone

from fhir.resources.R4B.auditevent import AuditEvent

from app.audit import EventoAuditoria, registrar

AHORA = datetime(2026, 11, 14, 22, 41, 7, tzinfo=timezone(timedelta(hours=-5)))


def test_registrar_crea_un_evento_con_quien_que_y_resultado():
    evento = registrar(AHORA, "Dr. Mateo Vargas", "Búsqueda en índice maestro", "3 registros", "ok")
    assert isinstance(evento, EventoAuditoria)
    assert evento.hora == AHORA
    assert evento.quien == "Dr. Mateo Vargas"
    assert evento.accion == "Búsqueda en índice maestro"
    assert evento.detalle == "3 registros"
    assert evento.resultado == "ok"


def test_el_id_es_determinista_y_distinto_por_accion():
    a = registrar(AHORA, "x", "Acción A", "d", "ok")
    b = registrar(AHORA, "x", "Acción A", "d", "ok")
    c = registrar(AHORA, "x", "Acción B", "d", "ok")
    assert a.id == b.id
    assert a.id != c.id
    assert a.id.startswith("aud-224107-")


def test_se_proyecta_a_un_auditevent_fhir_valido():
    evento = registrar(AHORA, "Adaptador FHIR", "Consulta a EPS Andina", "2 recursos", "ok")
    fhir = evento.a_fhir()
    assert isinstance(fhir, AuditEvent)
    assert fhir.id == evento.id
    assert fhir.recorded == AHORA
    assert fhir.agent[0].who.display == "Adaptador FHIR"
    assert fhir.agent[0].requestor is True
    assert fhir.source.observer.display == "Hilo Clínico"
    assert fhir.entity[0].name == "Consulta a EPS Andina"
    assert fhir.entity[0].description == "2 recursos"


def test_el_resultado_se_traduce_al_codigo_outcome_de_fhir():
    assert registrar(AHORA, "x", "a", "d", "ok").a_fhir().outcome == "0"
    assert registrar(AHORA, "x", "a", "d", "warn").a_fhir().outcome == "0"
    assert registrar(AHORA, "x", "a", "d", "deny").a_fhir().outcome == "4"
    assert registrar(AHORA, "x", "a", "d", "warn").a_fhir().outcomeDesc == "warn"
