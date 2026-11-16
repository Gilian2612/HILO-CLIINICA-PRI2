"""Utilidades compartidas por los adaptadores."""

from app.mpi import PacienteMaestro


def referencia_paciente(paciente: PacienteMaestro) -> dict:
    """Todos los recursos apuntan al paciente maestro, no al ID local de cada fuente."""
    return {"reference": f"Patient/{paciente.id}"}


def de_aaaammdd(fecha: str) -> str:
    return f"{fecha[0:4]}-{fecha[4:6]}-{fecha[6:8]}"


def de_ddmmaaaa(fecha: str) -> str:
    dia, mes, anio = fecha.split("/")
    return f"{anio}-{mes}-{dia}"


ZONA_COLOMBIA = "-05:00"


def de_fecha_hora_local(fecha_hora: str) -> str:
    """'2026-11-07T08:12' → '2026-11-07T08:12:00-05:00'.

    FHIR exige segundos y zona horaria cuando el dateTime trae hora. Las fuentes
    colombianas registran hora local sin zona, así que se asume Colombia (UTC-5).
    """
    if len(fecha_hora) == 16:  # AAAA-MM-DDTHH:MM
        fecha_hora += ":00"
    if not fecha_hora.endswith("Z") and fecha_hora[-6] not in "+-":
        fecha_hora += ZONA_COLOMBIA
    return fecha_hora
