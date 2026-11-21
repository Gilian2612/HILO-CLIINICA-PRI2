"""Sustituto mínimo de FastAPI para correr el backend dentro del navegador (Pyodide).

En latest.html no hay servidor HTTP: `despachador.py` llama directamente a las funciones de
`app/api/rutas.py`. Este módulo solo provee lo que `rutas.py` importa, y `APIRouter`
registra cada ruta (método, path, función, status_code) para que el despachador la encuentre.
"""


class HTTPException(Exception):
    def __init__(self, status_code: int, detail=None):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class Response:
    def __init__(self, content=None, status_code: int = 200, **_):
        self.content = content
        self.status_code = status_code


class status:  # noqa: N801 (mismo nombre que fastapi.status)
    HTTP_201_CREATED = 201
    HTTP_204_NO_CONTENT = 204


class APIRouter:
    def __init__(self, prefix: str = "", **_):
        self.prefix = prefix
        self.rutas: list[tuple[str, str, object, int]] = []

    def _registrar(self, metodo: str, path: str, status_code: int = 200, **_):
        def decorador(fn):
            self.rutas.append((metodo, self.prefix + path, fn, status_code))
            return fn

        return decorador

    def get(self, path, **kw):
        return self._registrar("GET", path, **kw)

    def post(self, path, **kw):
        return self._registrar("POST", path, **kw)

    def patch(self, path, **kw):
        return self._registrar("PATCH", path, **kw)

    def delete(self, path, **kw):
        return self._registrar("DELETE", path, **kw)
