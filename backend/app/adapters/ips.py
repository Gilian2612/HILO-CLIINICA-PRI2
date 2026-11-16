"""IPS (JSON propio) → AllergyIntolerance + Encounter + Condition + MedicationRequest."""

from fhir.resources.R4B.allergyintolerance import AllergyIntolerance
from fhir.resources.R4B.condition import Condition
from fhir.resources.R4B.encounter import Encounter
from fhir.resources.R4B.medicationrequest import MedicationRequest
from fhir.resources.R4B.resource import Resource

from app.adapters._comun import de_ddmmaaaa, referencia_paciente
from app.mpi import PacienteMaestro, normalizar_documento
from app.sources import FUENTES, ips

CIE10 = "http://hl7.org/fhir/sid/icd-10"
ALERGIA_CLINICA = "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"


def a_fhir(paciente: PacienteMaestro) -> list[Resource]:
    datos = ips.datos()
    local = next(
        (p for p in datos["pacientes"] if normalizar_documento(p["documento"]) == paciente.documento),
        None,
    )
    if not local:
        return []

    pid = local["id"]
    sujeto = referencia_paciente(paciente)
    recursos: list[Resource] = []

    for n, alergia in enumerate(_de(datos["alergias"], pid), start=1):
        grave = alergia["gravedad"] == "ALTA"
        recursos.append(
            AllergyIntolerance(
                id=f"alg-{pid}-{n}",
                clinicalStatus={"coding": [{"system": ALERGIA_CLINICA, "code": "active"}]},
                criticality="high" if grave else "low",
                code={"text": alergia["sustancia"]},
                patient=sujeto,
                recordedDate=de_ddmmaaaa(alergia["registrada"]),
                reaction=[
                    {
                        # FHIR exige al menos una manifestación; la fuente solo trae texto libre.
                        "manifestation": [{"text": alergia["reaccion"]}],
                        "description": alergia["reaccion"],
                        "severity": "severe" if grave else "mild",
                    }
                ],
            )
        )

    for n, atencion in enumerate(_de(datos["atenciones"], pid), start=1):
        encuentro_id = f"enc-{pid}-{n}"
        fecha = de_ddmmaaaa(atencion["fecha"])
        recursos.append(
            Encounter(
                id=encuentro_id,
                status="finished",
                **{"class": {"code": "AMB", "display": "Ambulatoria"}},
                type=[{"text": atencion["tipo"]}],
                subject=sujeto,
                period={"start": fecha},
                reasonCode=[{"text": atencion["motivo"]}],
                participant=[{"individual": {"display": atencion["profesional"]}}],
                serviceProvider={"display": FUENTES["ips"].nombre},
            )
        )
        recursos.append(
            Condition(
                id=f"cond-{pid}-{n}",
                code={
                    "coding": [{"system": CIE10, "code": atencion["cie10"], "display": atencion["dx"]}],
                    "text": atencion["dx"],
                },
                subject=sujeto,
                encounter={"reference": f"Encounter/{encuentro_id}"},
                recordedDate=fecha,
                note=[{"text": atencion["plan"]}] if atencion.get("plan") else None,
            )
        )

    for n, formula in enumerate(_de(datos["formulas"], pid), start=1):
        recursos.append(
            MedicationRequest(
                id=f"med-{pid}-{n}",
                status="active",
                intent="order",
                medicationCodeableConcept={"text": formula["medicamento"]},
                subject=sujeto,
                authoredOn=de_ddmmaaaa(formula["fecha"]),
                dosageInstruction=[{"text": formula["dosis"]}],
            )
        )

    return recursos


def _de(filas: list[dict], pid: str) -> list[dict]:
    return [f for f in filas if f["pid"] == pid]
