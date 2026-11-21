"""Línea de tiempo clínica: lo que el médico ve en el visor.

Se arma solo con los recursos que el consentimiento permitió traer. Agrupa los
exámenes de una misma orden en un item, une cada Encounter con su Condition, y deja
las alergias y la cobertura aparte porque se muestran en un lugar destacado.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from fhir.resources.R4B.coverage import Coverage
from fhir.resources.R4B.resource import Resource

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
DIAS_RECIENTE = 30


@dataclass
class Item:
    id: str
    fecha: str  # ISO, para ordenar
    tipo: str  # laboratorio | consulta | formula | autorizacion
    fuente: str  # eps | ips | lab
    titulo: str
    subtitulo: str
    detalle: list[tuple[str, str]]
    recursos: list[Resource]
    fecha_label: str = ""
    hace: str = ""
    reciente: bool = False
    analitos: list[dict] = field(default_factory=list)


@dataclass
class Alergia:
    sustancia: str
    reaccion: str
    critica: bool
    desde: str
    recurso: Resource
    fuente: str = "ips"


@dataclass
class LineaTiempo:
    items: list[Item]
    alergias: list[Alergia]
    cobertura: Coverage | None


def linea_de_tiempo(recursos: list[Resource], hoy: date) -> LineaTiempo:
    def de_tipo(tipo: str) -> list[Resource]:
        return [r for r in recursos if r.get_resource_type() == tipo]

    items: list[Item] = []

    observaciones = de_tipo("Observation")
    if observaciones:
        orden = observaciones[0].identifier[0].value
        items.append(
            Item(
                id=f"tl-lab-{orden}",
                fecha=_iso(observaciones[0].effectiveDateTime),
                tipo="laboratorio",
                fuente="lab",
                titulo="Hemograma y proteína C reactiva",
                subtitulo=f"{len(observaciones)} analitos · {observaciones[0].performer[0].display}",
                detalle=[("Orden", orden)],
                recursos=observaciones,
                analitos=[
                    {
                        "nombre": o.code.text,
                        "valor": float(o.valueQuantity.value),
                        "unidad": o.valueQuantity.unit,
                        "bandera": o.interpretation[0].coding[0].code,
                    }
                    for o in observaciones
                ],
            )
        )

    condiciones = de_tipo("Condition")
    for encuentro in de_tipo("Encounter"):
        condicion = next(
            (c for c in condiciones if c.encounter.reference == f"Encounter/{encuentro.id}"), None
        )
        detalle = [("Motivo", encuentro.reasonCode[0].text)]
        if condicion and condicion.note:
            detalle.append(("Plan", condicion.note[0].text))
        detalle.append(("Profesional", encuentro.participant[0].individual.display))
        codigo = condicion.code.coding[0] if condicion else None
        items.append(
            Item(
                id=f"tl-{encuentro.id}",
                fecha=_iso(encuentro.period.start),
                tipo="consulta",
                fuente="ips",
                titulo=encuentro.type[0].text,
                subtitulo=f"{codigo.code} · {codigo.display}" if codigo else "",
                detalle=detalle,
                recursos=[r for r in (encuentro, condicion) if r is not None],
            )
        )

    for formula in de_tipo("MedicationRequest"):
        items.append(
            Item(
                id=f"tl-{formula.id}",
                fecha=_iso(formula.authoredOn),
                tipo="formula",
                fuente="ips",
                titulo=formula.medicationCodeableConcept.text,
                subtitulo=formula.dosageInstruction[0].text,
                detalle=[("Tipo", "Fórmula médica")],
                recursos=[formula],
            )
        )

    for autorizacion in de_tipo("ServiceRequest"):
        items.append(
            Item(
                id=f"tl-{autorizacion.id}",
                fecha=_iso(autorizacion.authoredOn),
                tipo="autorizacion",
                fuente="eps",
                titulo=f"Autorización: {autorizacion.code.text}",
                subtitulo=f"{autorizacion.id} · aprobada, aún sin realizar",
                detalle=[("Estado", "Aprobada por la EPS")],
                recursos=[autorizacion],
            )
        )

    items.sort(key=lambda i: i.fecha, reverse=True)  # estable: los empates conservan su orden
    for item in items:
        fecha = _a_date(item.fecha)
        item.fecha_label = etiqueta_fecha(fecha)
        item.hace = hace(fecha, hoy)
        item.reciente = (hoy - fecha).days <= DIAS_RECIENTE

    alergias = [
        Alergia(
            sustancia=a.code.text,
            reaccion=a.reaction[0].description,
            critica=a.criticality == "high",
            desde=etiqueta_fecha(_a_date(_iso(a.recordedDate))),
            recurso=a,
        )
        for a in de_tipo("AllergyIntolerance")
    ]
    coberturas = de_tipo("Coverage")
    return LineaTiempo(items=items, alergias=alergias, cobertura=coberturas[0] if coberturas else None)


def etiqueta_fecha(fecha: date) -> str:
    """7 nov 2026"""
    return f"{fecha.day} {MESES[fecha.month - 1]} {fecha.year}"


def hace(fecha: date, hoy: date) -> str:
    """hoy · hace 7 días · hace 3 meses · hace 5 años"""
    dias = (hoy - fecha).days
    if dias == 0:
        return "hoy"
    if dias < 31:
        return f"hace {dias} días"
    if dias < 365:
        return f"hace {round(dias / 30)} meses"
    return f"hace {dias // 365} años"


def _iso(valor: date | datetime | str) -> str:
    return valor if isinstance(valor, str) else valor.isoformat()


def _a_date(iso: str) -> date:
    return date.fromisoformat(iso[:10])
