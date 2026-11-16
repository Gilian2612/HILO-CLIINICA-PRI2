"""Paso 7: la API expone el proceso al frontend. El frontend no decide nada: pide y muestra."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

INICIO = "2026-11-14T22:41:07-05:00"


@pytest.fixture
def client():
    return TestClient(app)


def crear(client, escenario="consentimiento"):
    respuesta = client.post("/api/simulaciones", json={"escenario": escenario, "inicio": INICIO})
    assert respuesta.status_code == 201
    return respuesta.json()


# Catálogos


def test_proceso_devuelve_el_modelo_bpmn_para_dibujar(client):
    datos = client.get("/api/proceso").json()
    assert len(datos["nodos"]) == 18
    assert len(datos["flujos"]) == 19
    assert len(datos["mensajes"]) == 5
    assert [c["id"] for c in datos["carriles"]] == ["lane_medico", "lane_hilo", "lane_paciente"]
    assert [p["id"] for p in datos["pools"]] == ["pool_fuentes", "pool_ihce"]
    buscar = next(n for n in datos["nodos"] if n["id"] == "t_buscar")
    assert buscar["kind"] == "user" and buscar["cx"] == 205
    assert [e["id"] for e in datos["escenarios"]] == ["consentimiento", "emergencia", "rechazo"]


def test_catalogo_devuelve_fuentes_categorias_medico_y_red(client):
    datos = client.get("/api/catalogo").json()
    assert [f["id"] for f in datos["fuentes"]] == ["eps", "ips", "lab"]
    assert datos["fuentes"][2]["formato"] == "CSV"
    assert [c["id"] for c in datos["categorias"]] == ["alergias", "laboratorios", "consultas", "eps"]
    assert datos["medico"]["nombre"] == "Dr. Mateo Vargas"
    assert datos["red"]["endpoint"] == "https://fhir.clinicadelpacifico.example/r4"
    assert len(datos["red"]["ips"]) == 6


# Ciclo de vida de una simulación


def test_crear_una_simulacion_arranca_esperando_al_medico(client):
    sim = crear(client)
    assert sim["id"]
    assert sim["escenario"] == "consentimiento"
    assert sim["nodo"] == "t_buscar" and sim["estado"] == "waiting"
    assert sim["visitados"] == ["start", "t_buscar"]
    assert sim["ctx"]["borrador"]["documento"] == "1032456789"
    assert sim["ctx"]["mpi"] is None
    assert sim["puede_volver"] is False


def test_crear_con_escenario_invalido_responde_422(client):
    assert client.post("/api/simulaciones", json={"escenario": "otro"}).status_code == 422


def test_simulacion_inexistente_responde_404(client):
    assert client.get("/api/simulaciones/no-existe").status_code == 404
    assert client.post("/api/simulaciones/no-existe/paso").status_code == 404


def test_paso_avanza_y_get_devuelve_lo_mismo(client):
    sim = crear(client)
    tras_paso = client.post(f"/api/simulaciones/{sim['id']}/paso").json()
    assert tras_paso["estado"] == "moving"
    assert tras_paso["en_movimiento"] == {"flujo": "f2", "desde": "t_buscar", "hacia": "t_mpi"}
    assert client.get(f"/api/simulaciones/{sim['id']}").json() == tras_paso


def test_actuar_con_documento_corto_deja_el_error_sin_avanzar(client):
    sim = crear(client)
    r = client.post(f"/api/simulaciones/{sim['id']}/actuar", json={"documento": "123"}).json()
    assert r["nodo"] == "t_buscar" and r["estado"] == "waiting"
    assert r["ctx"]["error_busqueda"] == "corto"


def test_borrador_se_edita_sin_mover_el_proceso_y_limpia_el_error(client):
    sim = crear(client)
    client.post(f"/api/simulaciones/{sim['id']}/actuar", json={"documento": "123"})
    r = client.patch(
        f"/api/simulaciones/{sim['id']}/borrador", json={"documento": "79845120", "emergencia": True}
    ).json()
    assert r["ctx"]["borrador"]["documento"] == "79845120"
    assert r["ctx"]["borrador"]["emergencia"] is True
    assert r["ctx"]["borrador"]["nota"].startswith("Antecedentes")  # lo no enviado se conserva
    assert r["ctx"]["error_busqueda"] is None
    assert r["nodo"] == "t_buscar"


def test_el_mpi_se_serializa_con_paciente_e_identidades(client):
    sim = crear(client)
    sid = sim["id"]
    client.post(f"/api/simulaciones/{sid}/paso")
    r = client.post(f"/api/simulaciones/{sid}/paso").json()
    assert r["nodo"] == "t_mpi"
    assert r["ctx"]["mpi"]["paciente"]["nombre"] == "Mariana Sofía López Castro"
    assert [i["fuente"] for i in r["ctx"]["mpi"]["identidades"]] == ["eps", "ips", "lab"]
    assert r["ctx"]["auditoria"][0]["accion"] == "Búsqueda en índice maestro"
    assert r["ctx"]["auditoria"][0]["hora"] == "2026-11-14T22:41:09-05:00"


def correr_hasta(client, sid, nodo):
    for _ in range(60):
        r = client.get(f"/api/simulaciones/{sid}").json()
        if r["estado"] == "ended" or (r["nodo"] == nodo and r["estado"] == "waiting"):
            return r
        r = client.post(f"/api/simulaciones/{sid}/paso").json()
    raise AssertionError("no llegó")


def test_la_paciente_responde_con_categorias_y_se_consulta_la_red(client):
    sid = crear(client)["id"]
    correr_hasta(client, sid, "t_resp")
    r = client.post(
        f"/api/simulaciones/{sid}/actuar", json={"decision": "granted", "categorias": ["alergias"]}
    ).json()
    assert r["ctx"]["consent"]["resourceType"] == "Consent"
    assert [c["code"] for c in r["ctx"]["consent"]["provision"]["class"]] == [
        "AllergyIntolerance",
        "MedicationRequest",
    ]
    r = correr_hasta(client, sid, "t_atender")
    assert r["nodo"] == "t_atender"
    assert {x["resourceType"] for x in r["ctx"]["recursos"]} == {"AllergyIntolerance", "MedicationRequest"}
    assert sum(1 for p in r["ctx"]["log"] if p["status"] == 403) == 5
    assert r["ctx"]["linea"]["alergias"][0]["sustancia"] == "Penicilina"
    assert r["ctx"]["linea"]["alergias"][0]["recurso"]["resourceType"] == "AllergyIntolerance"
    assert [i["tipo"] for i in r["ctx"]["linea"]["items"]] == ["formula"]
    assert r["ctx"]["linea"]["cobertura"] is None


def test_escenario_completo_hasta_el_final_con_rda(client):
    sid = crear(client, "emergencia")["id"]
    r = correr_hasta(client, sid, "end_ok")
    assert r["estado"] == "ended" and r["nodo"] == "end_ok"
    assert r["ctx"]["rda"]["type"] == "document"
    assert r["ctx"]["envio"] is None
    assert r["ctx"]["linea"]["items"][0]["tipo"] == "laboratorio"
    assert r["ctx"]["linea"]["items"][0]["analitos"][0]["bandera"] == "H"
    assert r["ctx"]["linea"]["cobertura"]["resourceType"] == "Coverage"
    assert len(r["ctx"]["auditoria"]) == 7
    assert client.post(f"/api/simulaciones/{sid}/paso").json() == r  # ya terminó: no cambia


def test_destino_ips_devuelve_el_bundle_de_envio(client):
    sid = crear(client)["id"]
    correr_hasta(client, sid, "t_atender")
    client.post(f"/api/simulaciones/{sid}/actuar", json={"nota": "Nota", "destino": "ips"})
    r = correr_hasta(client, sid, "end_ok")
    assert r["ctx"]["envio"]["type"] == "transaction"
    assert r["ctx"]["log"][-1] == {
        "fuente": "dest", "tipo": "Bundle", "metodo": "POST",
        "url": "https://fhir.clinicadelpacifico.example/r4", "status": 201, "cantidad": 3,
    }


def test_revocar_deja_el_consent_inactivo(client):
    sid = crear(client)["id"]
    correr_hasta(client, sid, "t_atender")
    r = client.post(f"/api/simulaciones/{sid}/revocar").json()
    assert r["ctx"]["consent"]["status"] == "inactive"
    assert r["ctx"]["revocado"] is True
    assert r["ctx"]["auditoria"][-1]["accion"] == "Acceso revocado"


# Paso atrás


def test_atras_vuelve_al_estado_anterior_conservando_el_borrador(client):
    sim = crear(client)
    sid = sim["id"]
    client.post(f"/api/simulaciones/{sid}/paso")
    tras_dos = client.post(f"/api/simulaciones/{sid}/paso").json()
    assert tras_dos["nodo"] == "t_mpi" and tras_dos["puede_volver"] is True
    client.patch(f"/api/simulaciones/{sid}/borrador", json={"nota": "cambiada"})
    r = client.post(f"/api/simulaciones/{sid}/atras").json()
    assert r["nodo"] == "t_buscar" and r["estado"] == "moving"
    assert r["ctx"]["mpi"] is not None  # la búsqueda ocurre al actuar en t_buscar
    assert r["ctx"]["auditoria"] == []  # la auditoría del MPI se escribe al llegar a t_mpi
    assert r["ctx"]["borrador"]["nota"] == "cambiada"
    r = client.post(f"/api/simulaciones/{sid}/atras").json()
    assert r["estado"] == "waiting" and r["puede_volver"] is False
    assert r["ctx"]["mpi"] is None
    assert client.post(f"/api/simulaciones/{sid}/atras").json() == r  # sin historial no hace nada


def test_un_paso_que_no_cambia_nada_no_entra_al_historial(client):
    sid = crear(client, "emergencia")["id"]
    correr_hasta(client, sid, "end_ok")
    antes = client.get(f"/api/simulaciones/{sid}").json()
    client.post(f"/api/simulaciones/{sid}/paso")
    client.post(f"/api/simulaciones/{sid}/revocar")  # emergencia activa: sí cambia
    r = client.post(f"/api/simulaciones/{sid}/atras").json()
    assert r == antes


def test_borrar_una_simulacion(client):
    sid = crear(client)["id"]
    assert client.delete(f"/api/simulaciones/{sid}").status_code == 204
    assert client.get(f"/api/simulaciones/{sid}").status_code == 404
