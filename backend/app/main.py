"""Punto de entrada de la API de Hilo Clínico.

Ejecutar en desarrollo:  uvicorn app.main:app --reload
Documentación interactiva: http://localhost:8000/docs
"""

from fastapi import FastAPI

from app.api.rutas import router

app = FastAPI(
    title="Hilo Clínico",
    version="0.1.0",
    description=(
        "Capa de interoperabilidad clínica: índice maestro de pacientes, consentimiento, "
        "adaptadores FHIR R4, auditoría y motor del proceso de atención."
    ),
)
app.include_router(router)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Comprueba que la API está arriba."""
    return {"status": "ok"}
