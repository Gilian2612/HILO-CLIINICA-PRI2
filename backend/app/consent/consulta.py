"""Consulta a la red respetando el consentimiento.

Por cada fuente y cada tipo de recurso se arma una petición FHIR. Si el tipo está
autorizado, el adaptador la resuelve (200). Si no, se registra un 403 y la fuente
no se consulta.
"""

from dataclasses import dataclass, field
from datetime import datetime

from fhir.resources.R4B.consent import Consent
from fhir.resources.R4B.resource import Resource

from app.adapters import ADAPTADORES
from app.consent.gestor import permite
from app.mpi import PacienteMaestro


@dataclass(frozen=True)
class Peticion:
    """Una línea del log de peticiones FHIR."""

    fuente: str
    tipo: str
    metodo: str
    url: str
    status: int  # 200 autorizado, 403 fuera del permiso
    cantidad: int


@dataclass
class ResultadoConsulta:
    log: list[Peticion] = field(default_factory=list)
    recursos: list[Resource] = field(default_factory=list)


def consultar_red(
    paciente: PacienteMaestro, consent: Consent | None, ahora: datetime
) -> ResultadoConsulta:
    resultado = ResultadoConsulta()
    for adaptador in ADAPTADORES.values():
        traidos: list[Resource] | None = None  # se consulta la fuente solo si hace falta
        for tipo in adaptador.tipos:
            autorizado = permite(consent, tipo, ahora)
            encontrados: list[Resource] = []
            if autorizado:
                if traidos is None:
                    traidos = adaptador.a_fhir(paciente)
                encontrados = [r for r in traidos if r.get_resource_type() == tipo]
            resultado.log.append(
                Peticion(
                    fuente=adaptador.fuente,
                    tipo=tipo,
                    metodo="GET",
                    url=url_de(tipo, paciente),
                    status=200 if autorizado else 403,
                    cantidad=len(encontrados),
                )
            )
            resultado.recursos.extend(encontrados)
    return resultado


def url_de(tipo: str, paciente: PacienteMaestro) -> str:
    """La búsqueda FHIR que se haría contra la fuente."""
    if tipo == "Coverage":
        return f"/Coverage?beneficiary={paciente.id}"
    if tipo == "Observation":
        return f"/Observation?patient={paciente.id}&category=laboratory"
    return f"/{tipo}?patient={paciente.id}"
