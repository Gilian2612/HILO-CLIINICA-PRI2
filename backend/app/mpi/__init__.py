"""Índice maestro de pacientes (MPI).

Une a la misma persona en EPS, IPS y laboratorio a partir de su documento,
aunque cada fuente la guarde con otro ID, otro formato de nombre y otra fecha.
"""

from app.mpi.indice import (
    DocumentoCorto,
    Identidad,
    PacienteMaestro,
    PacienteNoEncontrado,
    ResultadoBusqueda,
    buscar,
    normalizar_documento,
)

__all__ = [
    "DocumentoCorto",
    "Identidad",
    "PacienteMaestro",
    "PacienteNoEncontrado",
    "ResultadoBusqueda",
    "buscar",
    "normalizar_documento",
]
