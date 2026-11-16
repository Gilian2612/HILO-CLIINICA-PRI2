"""Laboratorio (CSV) → Observation de categoría laboratory."""

from fhir.resources.R4B.observation import Observation
from fhir.resources.R4B.resource import Resource

from app.adapters._comun import de_fecha_hora_local, referencia_paciente
from app.mpi import PacienteMaestro, normalizar_documento
from app.sources import FUENTES, lab

CATEGORIA = "http://terminology.hl7.org/CodeSystem/observation-category"
INTERPRETACION = "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"
TEXTO = {"H": "Alto", "L": "Bajo", "N": "Normal"}


def a_fhir(paciente: PacienteMaestro) -> list[Resource]:
    filas = [f for f in lab.filas() if normalizar_documento(f["doc_paciente"]) == paciente.documento]
    recursos: list[Resource] = []
    for n, fila in enumerate(filas, start=1):
        valor, ref_min, ref_max = float(fila["valor"]), float(fila["ref_min"]), float(fila["ref_max"])
        codigo = interpretar(valor, ref_min, ref_max)
        recursos.append(
            Observation(
                id=f"obs-{fila['orden']}-{n}",
                status="final",
                category=[{"coding": [{"system": CATEGORIA, "code": "laboratory"}]}],
                code={"text": fila["analito"]},
                subject=referencia_paciente(paciente),
                effectiveDateTime=de_fecha_hora_local(fila["fecha_hora"]),
                valueQuantity={"value": valor, "unit": fila["unidad"]},
                referenceRange=[{"low": {"value": ref_min}, "high": {"value": ref_max}}],
                interpretation=[
                    {"coding": [{"system": INTERPRETACION, "code": codigo}], "text": TEXTO[codigo]}
                ],
                performer=[{"display": FUENTES["lab"].nombre}],
                identifier=[{"value": fila["orden"]}],
            )
        )
    return recursos


def interpretar(valor: float, ref_min: float, ref_max: float) -> str:
    """H si está por encima del rango, L si por debajo, N si dentro."""
    if valor > ref_max:
        return "H"
    if valor < ref_min:
        return "L"
    return "N"
