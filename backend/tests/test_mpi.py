"""Paso 2: el índice maestro de pacientes une a la misma persona en las tres fuentes."""

import pytest

from app.mpi import DocumentoCorto, PacienteNoEncontrado, buscar, normalizar_documento


def test_normalizar_documento_deja_solo_digitos():
    assert normalizar_documento("CC-1.032.456.789") == "1032456789"
    assert normalizar_documento("CC 1032456789") == "1032456789"
    assert normalizar_documento(" 1032456789 ") == "1032456789"
    assert normalizar_documento(None) == ""


def test_documento_corto_no_se_busca():
    with pytest.raises(DocumentoCorto):
        buscar("12345")


def test_documento_desconocido_no_existe():
    with pytest.raises(PacienteNoEncontrado):
        buscar("9999999999")


def test_mariana_se_encuentra_en_las_tres_fuentes():
    resultado = buscar("CC-1.032.456.789")
    assert resultado.paciente.completo is True
    assert {i.fuente for i in resultado.identidades} == {"eps", "ips", "lab"}


def test_cada_fuente_conoce_a_mariana_con_otro_id():
    por_fuente = {i.fuente: i for i in buscar("1032456789").identidades}
    assert por_fuente["eps"].id_local == "CC 1032456789"
    assert por_fuente["ips"].id_local == "P-00417"
    assert por_fuente["lab"].id_local == "LB-2291"


def test_paciente_maestro_normaliza_nombre_fecha_y_sexo():
    paciente = buscar("1032456789").paciente
    assert paciente.id == "hc-1032456789"
    assert paciente.documento == "1032456789"
    assert paciente.documento_label == "CC 1.032.456.789"
    assert paciente.nombre == "Mariana Sofía López Castro"
    assert paciente.nombres == "Mariana Sofía"
    assert paciente.fecha_nacimiento == "1992-03-14"
    assert paciente.sexo == "female"


def test_jorge_solo_esta_en_la_eps_y_queda_incompleto():
    resultado = buscar("79845120")
    assert resultado.paciente.completo is False
    assert [i.fuente for i in resultado.identidades] == ["eps"]
    assert resultado.paciente.nombre == "Jorge Eliecer Pardo Ruiz"
    assert resultado.paciente.fecha_nacimiento == "1971-09-02"
    assert resultado.paciente.sexo == "male"
