"""Envío de la atención al sistema propio de la IPS: Bundle de tipo transaction.

Se arma a partir del RDA: el Encounter y la ClinicalImpression se crean en la IPS por POST,
y una Provenance deja constancia de que el origen es Hilo Clínico. Hilo Clínico guarda
solo la referencia.
"""

from datetime import datetime

from fhir.resources.R4B.bundle import Bundle

from app.fhir.rda import solo_digitos

SISTEMA_ATENCION = "https://hiloclinico.co/atencion"


def crear_envio_ips(rda: Bundle, ahora: datetime) -> Bundle:
    sello = solo_digitos(ahora.isoformat())[:14]
    url_encounter = f"urn:uuid:enc-{sello}"
    url_impresion = f"urn:uuid:ci-{sello}"

    encounter = _recurso_de(rda, "Encounter")
    impresion = _recurso_de(rda, "ClinicalImpression")

    entradas = [
        {
            "fullUrl": url_encounter,
            "resource": {
                **encounter,
                "identifier": [{"system": SISTEMA_ATENCION, "value": f"HC-{sello}"}],
            },
            "request": {"method": "POST", "url": "Encounter"},
        },
        {
            "fullUrl": url_impresion,
            "resource": {**impresion, "encounter": {"reference": url_encounter}},
            "request": {"method": "POST", "url": "ClinicalImpression"},
        },
        {
            "fullUrl": f"urn:uuid:prov-{sello}",
            "resource": {
                "resourceType": "Provenance",
                "target": [{"reference": url_encounter}, {"reference": url_impresion}],
                "recorded": ahora,
                "agent": [
                    {
                        "type": {"text": "Origen"},
                        "who": {"display": "Hilo Clínico (capa de interoperabilidad)"},
                    }
                ],
                "reason": [
                    {"text": "Atención registrada en el sistema propio de la IPS por solicitud del cliente"}
                ],
            },
            "request": {"method": "POST", "url": "Provenance"},
        },
    ]
    return Bundle(id=f"envio-{sello}", type="transaction", timestamp=ahora, entry=entradas)


def _recurso_de(bundle: Bundle, tipo: str) -> dict:
    """Copia (como dict FHIR) del primer recurso de ese tipo dentro del bundle."""
    recurso = next(e.resource for e in bundle.entry if e.resource.get_resource_type() == tipo)
    return recurso.model_dump(by_alias=True, exclude_none=True)
