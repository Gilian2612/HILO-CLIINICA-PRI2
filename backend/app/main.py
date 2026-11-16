"""Punto de entrada de la API de Hilo Clínico.

Ejecutar en desarrollo:  uvicorn app.main:app --reload
Documentación interactiva: http://localhost:8000/docs
"""

from fastapi import FastAPI

app = FastAPI(title="Hilo Clínico", version="0.1.0")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Comprueba que la API está arriba."""
    return {"status": "ok"}
