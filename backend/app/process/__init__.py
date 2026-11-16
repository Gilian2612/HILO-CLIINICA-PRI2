"""Motor del proceso BPMN TO-BE.

- `modelo`: nodos, carriles, flujos y la lógica de las compuertas (una sola fuente de verdad
  para el motor y para el diagrama que dibuja el frontend).
- `motor`: la máquina de estados que recorre el proceso y ejecuta el efecto de cada nodo.
"""

from app.process.modelo import (
    CARRILES,
    FLUJOS,
    MENSAJES,
    NODOS,
    POOLS,
    Flujo,
    Nodo,
    flujo_entre,
    siguiente,
)
from app.process.motor import (
    ESCENARIOS,
    Borrador,
    Contexto,
    Escenario,
    Movimiento,
    Simulacion,
    actuar,
    completar,
    correr,
    llegar,
    nueva_simulacion,
    paso,
    revocar_acceso,
)

__all__ = [
    "CARRILES",
    "ESCENARIOS",
    "FLUJOS",
    "MENSAJES",
    "NODOS",
    "POOLS",
    "Borrador",
    "Contexto",
    "Escenario",
    "Flujo",
    "Movimiento",
    "Nodo",
    "Simulacion",
    "actuar",
    "completar",
    "correr",
    "flujo_entre",
    "llegar",
    "nueva_simulacion",
    "paso",
    "revocar_acceso",
    "siguiente",
]
