"""Creación, verificación y revocación del Consent FHIR."""

from datetime import datetime, timedelta
from typing import Literal

from fhir.resources.R4B.consent import Consent

from app.actores import MEDICO, Profesional
from app.consent.categorias import tipos_de
from app.mpi import PacienteMaestro

VIGENCIA = timedelta(hours=24)

Modo = Literal["paciente", "emergencia"]

LOINC = "http://loinc.org"
PARTICIPACION = "http://terminology.hl7.org/CodeSystem/v3-ParticipationType"


def crear_consentimiento(
    paciente: PacienteMaestro,
    categorias: list[str],
    modo: Modo,
    ahora: datetime,
    *,
    medico: Profesional = MEDICO,
) -> Consent:
    """Arma un Consent R4 que permite al médico (`medico`) ver los tipos de las categorías elegidas.

    - modo "paciente": lo otorga la paciente desde su app.
    - modo "emergencia": lo abre el médico por urgencia vital, sin autorización previa.
    """
    emergencia = modo == "emergencia"
    return Consent(
        id=f"consent-{paciente.documento}-{modo}",
        status="active",
        scope={
            "text": "Acceso de emergencia (urgencia vital)"
            if emergencia
            else "Autorización de la paciente"
        },
        category=[{"coding": [{"system": LOINC, "code": "59284-0", "display": "Consent Document"}]}],
        patient={"reference": f"Patient/{paciente.id}"},
        dateTime=ahora,
        performer=[{"display": medico.nombre if emergencia else paciente.nombre}],
        provision={
            "type": "permit",
            "period": {"start": ahora, "end": ahora + VIGENCIA},
            "actor": [
                {
                    "role": {"coding": [{"system": PARTICIPACION, "code": "PRCP"}]},
                    "reference": {"display": medico.display},
                }
            ],
            "class": [{"code": tipo} for tipo in tipos_de(categorias)],
        },
    )


def permite(consent: Consent | None, tipo: str, ahora: datetime) -> bool:
    """Regla central: hay un Consent activo, vigente, que incluye este tipo de recurso."""
    if consent is None or consent.status != "active":
        return False
    periodo = consent.provision.period
    if periodo.start is not None and ahora < periodo.start:
        return False
    if periodo.end is not None and ahora > periodo.end:
        return False
    return any(c.code == tipo for c in consent.provision.class_fhir or [])


def revocar(consent: Consent) -> Consent:
    """Devuelve una copia inactiva. A partir de ahí nada se permite."""
    return consent.model_copy(update={"status": "inactive"})
