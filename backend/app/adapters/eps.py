"""EPS (tabla plana) → Coverage + ServiceRequest."""

from fhir.resources.R4B.coverage import Coverage
from fhir.resources.R4B.resource import Resource
from fhir.resources.R4B.servicerequest import ServiceRequest

from app.adapters._comun import de_aaaammdd, referencia_paciente
from app.mpi import PacienteMaestro, normalizar_documento
from app.sources import FUENTES, eps


def a_fhir(paciente: PacienteMaestro) -> list[Resource]:
    afiliado = next(
        (a for a in eps.afiliados() if normalizar_documento(a["num_doc"]) == paciente.documento),
        None,
    )
    if not afiliado:
        return []

    cobertura_id = f"cov-{afiliado['num_doc']}"
    recursos: list[Resource] = [
        Coverage(
            id=cobertura_id,
            status="active" if afiliado["estado"] == "AC" else "cancelled",
            type={
                "text": "Régimen contributivo"
                if afiliado["regimen"] == "C"
                else "Régimen subsidiado"
            },
            beneficiary=referencia_paciente(paciente),
            payor=[{"display": FUENTES["eps"].nombre}],
        )
    ]

    for aut in eps.autorizaciones():
        if normalizar_documento(aut["num_doc"]) != paciente.documento:
            continue
        recursos.append(
            ServiceRequest(
                id=aut["codigo"],
                status="active" if aut["estado"] == "APROBADA" else "on-hold",
                intent="order",
                code={"text": aut["servicio"]},
                subject=referencia_paciente(paciente),
                authoredOn=de_aaaammdd(aut["fecha"]),
                insurance=[{"reference": f"Coverage/{cobertura_id}"}],
            )
        )
    return recursos
