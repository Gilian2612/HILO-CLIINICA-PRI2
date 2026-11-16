"""Búsqueda en el índice maestro."""

import re
from dataclasses import dataclass

from app.sources import eps, ips, lab

LARGO_MINIMO = 6


class DocumentoCorto(ValueError):
    """El documento tiene menos de 6 dígitos: no se busca."""


class PacienteNoEncontrado(LookupError):
    """Ninguna fuente de la red reconoce el documento."""


@dataclass(frozen=True)
class Identidad:
    """Cómo conoce una fuente a la persona."""

    fuente: str  # "eps" | "ips" | "lab"
    id_local: str  # el ID con que la fuente la guarda
    como: str  # el nombre tal como lo tiene la fuente
    nacimiento: str | None  # la fecha tal como la tiene la fuente


@dataclass(frozen=True)
class PacienteMaestro:
    """La persona unificada. Es el `Patient/{id}` al que apuntan todos los recursos FHIR."""

    id: str  # hc-{documento}
    documento: str  # solo dígitos
    documento_label: str  # "CC 1.032.456.789"
    nombre: str  # "Mariana Sofía López Castro"
    nombres: str  # "Mariana Sofía"
    fecha_nacimiento: str  # ISO: 1992-03-14
    sexo: str  # FHIR: female | male
    completo: bool  # True si las tres fuentes la reconocen


@dataclass(frozen=True)
class ResultadoBusqueda:
    paciente: PacienteMaestro
    identidades: list[Identidad]


def normalizar_documento(valor: str | None) -> str:
    """Deja solo los dígitos: 'CC-1.032.456.789' → '1032456789'."""
    return re.sub(r"\D", "", str(valor or ""))


def buscar(documento: str) -> ResultadoBusqueda:
    """Busca el documento en las tres fuentes y devuelve el paciente unificado."""
    doc = normalizar_documento(documento)
    if len(doc) < LARGO_MINIMO:
        raise DocumentoCorto(documento)

    afiliado = next((a for a in eps.afiliados() if normalizar_documento(a["num_doc"]) == doc), None)
    datos_ips = ips.datos()
    paciente_ips = next(
        (p for p in datos_ips["pacientes"] if normalizar_documento(p["documento"]) == doc), None
    )
    filas_lab = [f for f in lab.filas() if normalizar_documento(f["doc_paciente"]) == doc]

    identidades: list[Identidad] = []
    if afiliado:
        identidades.append(
            Identidad(
                fuente="eps",
                id_local=f"{afiliado['tipo_doc']} {afiliado['num_doc']}",
                como=f"{afiliado['apellidos']} {afiliado['nombres']}",
                nacimiento=afiliado["fec_nac"],
            )
        )
    if paciente_ips:
        identidades.append(
            Identidad(
                fuente="ips",
                id_local=paciente_ips["id"],
                como=paciente_ips["nombre"],
                nacimiento=paciente_ips["nacimiento"],
            )
        )
    if filas_lab:
        identidades.append(
            Identidad(
                fuente="lab",
                id_local=filas_lab[0]["orden"],
                como=f"doc {filas_lab[0]['doc_paciente']}",
                nacimiento=None,
            )
        )
    if not identidades:
        raise PacienteNoEncontrado(documento)

    # La IPS tiene el nombre con tildes; la EPS lo tiene en mayúsculas sin tildes.
    # Se prefiere la IPS para el nombre y la EPS para la fecha (ya viene sin ambigüedad).
    if paciente_ips:
        apellidos, nombres = paciente_ips["nombre"].split(", ")
        nombre = f"{nombres} {apellidos}"
    else:
        nombres = _capitalizar(afiliado["nombres"])
        nombre = _capitalizar(f"{afiliado['nombres']} {afiliado['apellidos']}")

    if afiliado:
        fecha_nacimiento = _de_aaaammdd(afiliado["fec_nac"])
    else:
        fecha_nacimiento = _de_ddmmaaaa(paciente_ips["nacimiento"])

    sexo_nativo = (afiliado or paciente_ips)["sexo"]

    paciente = PacienteMaestro(
        id=f"hc-{doc}",
        documento=doc,
        documento_label=f"CC {int(doc):,}".replace(",", "."),
        nombre=nombre,
        nombres=nombres,
        fecha_nacimiento=fecha_nacimiento,
        sexo="female" if sexo_nativo == "F" else "male",
        completo=len(identidades) == 3,
    )
    return ResultadoBusqueda(paciente=paciente, identidades=identidades)


def _capitalizar(texto: str) -> str:
    """'MARIANA SOFIA' → 'Mariana Sofia'."""
    return " ".join(p.capitalize() for p in texto.lower().split())


def _de_aaaammdd(fecha: str) -> str:
    return f"{fecha[0:4]}-{fecha[4:6]}-{fecha[6:8]}"


def _de_ddmmaaaa(fecha: str) -> str:
    dia, mes, anio = fecha.split("/")
    return f"{anio}-{mes}-{dia}"
