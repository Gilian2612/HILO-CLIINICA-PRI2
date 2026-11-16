"""Resumen Digital de Atención (RDA): Bundle de tipo document.

Contiene la Composition que lo describe, el Encounter de urgencias, la alergia relevante
(si la hubo) y la ClinicalImpression con la nota del médico.
"""

import re
from datetime import datetime

from fhir.resources.R4B.bundle import Bundle
from fhir.resources.R4B.resource import Resource

from app.actores import MEDICO
from app.mpi import PacienteMaestro

MOTIVO_URGENCIAS = "Dolor abdominal y fiebre"


def solo_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor)


def crear_rda(
    paciente: PacienteMaestro, nota: str, ahora: datetime, recursos: list[Resource]
) -> Bundle:
    sello = solo_digitos(ahora.isoformat())[:12]
    sujeto = {"reference": f"Patient/{paciente.id}"}
    alergia = next((r for r in recursos if r.get_resource_type() == "AllergyIntolerance"), None)

    entradas = [
        {
            "fullUrl": f"urn:uuid:comp-{sello}",
            "resource": {
                "resourceType": "Composition",
                "status": "final",
                "type": {"text": "Resumen Digital de Atención en Salud (RDA)"},
                "subject": sujeto,
                "date": ahora,
                "author": [{"display": MEDICO.display}],
                "title": "Atención de urgencias",
            },
        },
        {
            "fullUrl": f"urn:uuid:enc-{sello}",
            "resource": {
                "resourceType": "Encounter",
                "status": "finished",
                "class": {"code": "EMER", "display": "Urgencias"},
                "subject": sujeto,
                "period": {"start": ahora},
                "serviceProvider": {"display": f"{MEDICO.organizacion}, {MEDICO.ciudad}"},
                "reasonCode": [{"text": MOTIVO_URGENCIAS}],
            },
        },
    ]
    if alergia is not None:
        entradas.append({"fullUrl": f"urn:uuid:{alergia.id}", "resource": alergia})
    entradas.append(
        {
            "fullUrl": f"urn:uuid:ci-{sello}",
            "resource": {
                "resourceType": "ClinicalImpression",
                "status": "completed",
                "subject": sujeto,
                "date": ahora,
                "summary": nota,
            },
        }
    )
    return Bundle(
        id=f"rda-{paciente.documento}-{sello}",
        type="document",
        timestamp=ahora,
        entry=entradas,
    )
