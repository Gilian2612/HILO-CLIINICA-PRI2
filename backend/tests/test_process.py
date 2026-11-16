"""Paso 6: el motor recorre el proceso BPMN TO-BE nodo por nodo."""

from datetime import datetime, timedelta, timezone

import pytest

from app.process import (
    FLUJOS,
    NODOS,
    actuar,
    correr,
    flujo_entre,
    nueva_simulacion,
    paso,
    revocar_acceso,
    siguiente,
)

INICIO = datetime(2026, 11, 14, 22, 41, 7, tzinfo=timezone(timedelta(hours=-5)))


# Modelo BPMN


def test_el_modelo_tiene_los_nodos_del_diagrama():
    assert len(NODOS) == 18  # 2 eventos de inicio/fin + 1 fin alterno + 5 compuertas + 10 tareas
    assert NODOS["start"].kind == "start"
    assert NODOS["t_buscar"].kind == "user"
    assert NODOS["t_buscar"].carril == "lane_medico"
    assert NODOS["t_solic"].kind == "send"
    assert NODOS["g_urg"].kind == "xor"
    assert NODOS["t_resp"].carril == "lane_paciente"
    assert NODOS["end_ok"].kind == "end"


def test_todos_los_flujos_conectan_nodos_existentes():
    for flujo in FLUJOS:
        assert flujo.desde in NODOS, flujo.id
        assert flujo.hacia in NODOS, flujo.id
    assert flujo_entre("g_urg", "t_emerg").nombre == "Sí"
    assert flujo_entre("g_aut", "end_no").nombre == "No"
    assert flujo_entre("start", "t_fhir") is None


def test_las_compuertas_deciden_segun_el_contexto():
    assert siguiente("g_urg", emergencia=True) == "t_emerg"
    assert siguiente("g_urg", emergencia=False) == "t_solic"
    assert siguiente("g_aut", decision="granted") == "g_join"
    assert siguiente("g_aut", decision="denied") == "end_no"
    assert siguiente("g_dest", destino="ips") == "t_envio"
    assert siguiente("g_dest", destino="hilo") == "t_guardar"
    assert siguiente("t_cerrar") == "end_ok"
    assert siguiente("end_ok") is None


# Motor: arranque y pasos


def test_la_simulacion_arranca_esperando_al_medico():
    sim = nueva_simulacion("consentimiento", INICIO)
    assert sim.nodo == "t_buscar"
    assert sim.estado == "waiting"
    assert sim.visitados == ["start", "t_buscar"]
    assert sim.ctx.borrador.documento == "1032456789"
    assert sim.ctx.borrador.emergencia is False


def test_un_documento_corto_no_avanza_y_deja_el_error():
    sim = nueva_simulacion("consentimiento", INICIO)
    actuar(sim, documento="123")
    assert sim.nodo == "t_buscar"
    assert sim.estado == "waiting"
    assert sim.ctx.error_busqueda == "corto"


def test_actuar_fuera_de_una_tarea_de_usuario_no_hace_nada():
    sim = nueva_simulacion("consentimiento", INICIO)
    actuar(sim)  # t_buscar
    assert sim.estado == "moving"
    antes = sim.nodo
    actuar(sim, decision="denied")
    assert sim.nodo == antes and sim.estado == "moving"


def test_paso_a_paso_desde_buscar_hasta_pedir_permiso():
    sim = nueva_simulacion("consentimiento", INICIO)
    paso(sim)  # actúa en t_buscar → moving
    assert sim.estado == "moving" and sim.en_movimiento.hacia == "t_mpi"
    paso(sim)  # llega a t_mpi → running
    assert sim.nodo == "t_mpi" and sim.estado == "running"
    assert sim.ctx.mpi.paciente.nombre == "Mariana Sofía López Castro"
    assert sim.ctx.auditoria[-1].accion == "Búsqueda en índice maestro"
    paso(sim)  # termina t_mpi → moving hacia g_urg
    paso(sim)  # llega a g_urg
    paso(sim)  # sale de g_urg por "No"
    paso(sim)  # llega a t_solic
    paso(sim)  # termina t_solic
    paso(sim)  # llega a t_resp
    assert sim.nodo == "t_resp" and sim.estado == "waiting"
    assert sim.ctx.solicitud == "pending"
    assert sim.flujos[-1] == "f6"


# Los tres escenarios de punta a punta


def test_escenario_con_autorizacion():
    sim = correr("consentimiento", INICIO)
    assert sim.estado == "ended" and sim.nodo == "end_ok"
    assert sim.visitados == [
        "start", "t_buscar", "t_mpi", "g_urg", "t_solic", "t_resp", "g_aut", "g_join",
        "t_fhir", "t_atender", "g_dest", "t_guardar", "g_dj", "t_cerrar", "end_ok",
    ]
    assert sim.ctx.consent.scope.text == "Autorización de la paciente"
    assert sim.ctx.decision == "granted"
    assert len(sim.ctx.recursos) == 12
    assert sim.ctx.linea.alergias[0].sustancia == "Penicilina"
    assert sim.ctx.rda.type == "document"
    assert sim.ctx.envio is None
    acciones = [e.accion for e in sim.ctx.auditoria]
    assert acciones == [
        "Búsqueda en índice maestro",
        "Solicitud enviada a la paciente",
        "Autorización concedida",
        "Consulta a EPS Andina",
        "Consulta a Centro Médico Chapinero",
        "Consulta a Laboratorio Bioandes",
        "Atención guardada",
        "RDA enviado al IHCE",
    ]
    assert sim.ctx.auditoria[2].quien == "Mariana Sofía López Castro"


def test_escenario_urgencia_vital():
    sim = correr("emergencia", INICIO)
    assert sim.nodo == "end_ok"
    assert "t_emerg" in sim.visitados and "t_resp" not in sim.visitados
    assert sim.ctx.consent.scope.text == "Acceso de emergencia (urgencia vital)"
    assert sim.ctx.auditoria[1].accion == "Acceso de emergencia abierto"
    assert sim.ctx.auditoria[1].resultado == "warn"
    assert len(sim.ctx.recursos) == 12


def test_escenario_rechazo():
    sim = correr("rechazo", INICIO)
    assert sim.estado == "ended" and sim.nodo == "end_no"
    assert sim.ctx.decision == "denied"
    assert sim.ctx.consent is None
    assert sim.ctx.recursos == []
    assert sim.ctx.auditoria[-1].accion == "Acceso denegado"
    assert sim.ctx.auditoria[-1].resultado == "deny"


def test_permiso_parcial_solo_trae_lo_autorizado():
    sim = correr("consentimiento", INICIO, hasta="t_resp")
    actuar(sim, decision="granted", categorias=["alergias"])
    correr(sim)
    tipos = {r.get_resource_type() for r in sim.ctx.recursos}
    assert tipos == {"AllergyIntolerance", "MedicationRequest"}
    assert sum(1 for p in sim.ctx.log if p.status == 403) == 5
    assert sim.ctx.auditoria[3].detalle == "Fuera del permiso de la paciente: no se consultó"


def test_destino_ips_envia_un_bundle_y_registra_201():
    sim = correr("consentimiento", INICIO, hasta="t_atender")
    actuar(sim, nota="Nota de prueba", destino="ips")
    correr(sim)
    assert "t_envio" in sim.visitados and "t_guardar" not in sim.visitados
    assert sim.ctx.envio.type == "transaction"
    assert sim.ctx.log[-1].metodo == "POST" and sim.ctx.log[-1].status == 201
    assert sim.ctx.log[-1].url == "https://fhir.clinicadelpacifico.example/r4"
    assert sim.ctx.auditoria[-2].accion == "Atención enviada al sistema de la IPS"
    assert sim.ctx.rda.entry[3].resource.summary == "Nota de prueba"


# Revocación y reloj


def test_la_paciente_puede_revocar_y_el_medico_deja_de_ver():
    sim = correr("consentimiento", INICIO, hasta="t_atender")
    assert sim.ctx.consent.status == "active"
    revocar_acceso(sim)
    assert sim.ctx.consent.status == "inactive"
    assert sim.ctx.revocado is True
    assert sim.ctx.auditoria[-1].accion == "Acceso revocado"
    revocar_acceso(sim)  # revocar dos veces no duplica la auditoría
    assert sum(1 for e in sim.ctx.auditoria if e.accion == "Acceso revocado") == 1


def test_sin_consentimiento_no_hay_nada_que_revocar():
    sim = nueva_simulacion("consentimiento", INICIO)
    revocar_acceso(sim)
    assert sim.ctx.auditoria == []


def test_el_reloj_avanza_con_cada_paso_del_proceso():
    sim = correr("consentimiento", INICIO)
    horas = [e.hora for e in sim.ctx.auditoria]
    assert horas == sorted(horas)
    assert horas[0] == INICIO + timedelta(seconds=2)
    assert sim.ctx.consent.provision.period.start > INICIO


@pytest.mark.parametrize("escenario", ["consentimiento", "emergencia", "rechazo"])
def test_correr_termina_siempre(escenario):
    assert correr(escenario, INICIO).estado == "ended"
