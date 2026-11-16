"""Almacén en memoria de simulaciones, con historial para el paso atrás.

Cada mutación guarda una copia del estado anterior solo si algo cambió. En una fase
posterior este almacén se reemplaza por una base de datos sin tocar las rutas.
"""

import copy
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

from app.api.esquemas import serializar_simulacion
from app.process import Simulacion


@dataclass
class Entrada:
    sim: Simulacion
    historial: list[Simulacion] = field(default_factory=list)


class Almacen:
    def __init__(self) -> None:
        self._entradas: dict[str, Entrada] = {}

    def crear(self, sim: Simulacion) -> str:
        id = uuid.uuid4().hex[:12]
        self._entradas[id] = Entrada(sim)
        return id

    def obtener(self, id: str) -> Entrada | None:
        return self._entradas.get(id)

    def borrar(self, id: str) -> bool:
        return self._entradas.pop(id, None) is not None

    def mutar(self, entrada: Entrada, accion: Callable[[Simulacion], object]) -> None:
        """Aplica `accion` y, si el estado cambió, guarda el anterior en el historial."""
        anterior = copy.deepcopy(entrada.sim)
        accion(entrada.sim)
        if serializar_simulacion("", entrada.sim, False) != serializar_simulacion("", anterior, False):
            entrada.historial.append(anterior)

    def atras(self, entrada: Entrada) -> None:
        """Vuelve al estado anterior conservando lo que el usuario tiene escrito."""
        if not entrada.historial:
            return
        borrador = entrada.sim.ctx.borrador
        entrada.sim = entrada.historial.pop()
        entrada.sim.ctx.borrador = borrador

    def serializar(self, id: str, entrada: Entrada) -> dict:
        return serializar_simulacion(id, entrada.sim, bool(entrada.historial))


almacen = Almacen()
