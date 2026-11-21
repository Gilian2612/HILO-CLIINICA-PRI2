"""Atiende las peticiones /api/... del frontend dentro del navegador, sin servidor.

El JavaScript de latest.html intercepta `fetch('/api/...')` y llama a `atender_json`, que
busca la ruta registrada en `app.api.rutas.router`, arma los argumentos (parámetros del
path y cuerpo validado con su modelo pydantic) y devuelve `[status, cuerpo_json]`.
Es la misma lógica del backend desplegado: solo cambia el transporte.
"""

import inspect
import json
import re
import typing

from fastapi import HTTPException, Response
from pydantic import BaseModel, ValidationError

from app.api.rutas import router


def _patron(path: str) -> re.Pattern:
    return re.compile("^" + re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", path) + "$")


RUTAS = [(metodo, _patron(path), fn, codigo) for metodo, path, fn, codigo in router.rutas]


def atender(metodo: str, path: str, cuerpo: str | None) -> tuple[int, str | None]:
    if path == "/api/health":  # en el backend vive en app/main.py, que aquí no se carga
        return 200, json.dumps({"status": "ok", "modo": "navegador"})
    for metodo_ruta, patron, fn, codigo in RUTAS:
        coincide = patron.match(path)
        if metodo_ruta != metodo.upper() or not coincide:
            continue
        try:
            tipos = typing.get_type_hints(fn)
            argumentos = {}
            for nombre in inspect.signature(fn).parameters:
                tipo = tipos.get(nombre)
                if nombre in coincide.groupdict():
                    argumentos[nombre] = coincide.group(nombre)
                elif isinstance(tipo, type) and issubclass(tipo, BaseModel):
                    argumentos[nombre] = tipo.model_validate_json(cuerpo or "{}")
            resultado = fn(**argumentos)
        except HTTPException as e:
            return e.status_code, json.dumps({"detail": e.detail})
        except ValidationError as e:
            return 422, json.dumps({"detail": json.loads(e.json())})
        if isinstance(resultado, Response):
            return resultado.status_code, None
        return codigo, json.dumps(resultado, default=str, ensure_ascii=False)
    return 404, json.dumps({"detail": "Not Found"})


def atender_json(metodo: str, path: str, cuerpo: str | None) -> str:
    """Lo que llama JavaScript: devuelve '[status, cuerpo]' como JSON."""
    return json.dumps(atender(metodo, path, cuerpo))
