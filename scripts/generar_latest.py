"""Genera latest.html: la última versión de Hilo Clínico en un solo archivo, sin servidor.

- El frontend (React) se compila con Vite y se incrusta: JS, CSS, fuentes y SVG en base64.
- El backend (todo `backend/app`) se incrusta como código fuente y corre en el navegador con
  Pyodide (Python en WebAssembly). `scripts/navegador/despachador.py` atiende las llamadas
  `/api/...` con las mismas funciones de `app/api/rutas.py`; `scripts/navegador/fastapi.py`
  reemplaza a FastAPI, que en el navegador no hace falta.

Necesita internet al abrirlo: Pyodide se descarga de jsDelivr y `fhir.resources` de PyPI.

Uso (desde la raíz del repo):
    python3 scripts/generar_latest.py              # compila el frontend y genera latest.html
    python3 scripts/generar_latest.py --sin-build  # usa frontend/dist tal como está
"""

import base64
import json
import mimetypes
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FRONTEND = RAIZ / "frontend"
DIST = FRONTEND / "dist"
BACKEND_APP = RAIZ / "backend" / "app"
NAVEGADOR = Path(__file__).resolve().parent / "navegador"
SALIDA = RAIZ / "latest.html"

PYODIDE = "https://cdn.jsdelivr.net/pyodide/v314.0.8/full/"
PAQUETES_PYODIDE = ["micropip", "pydantic"]
PAQUETES_PYPI = ["fhir-core==1.1.12", "fhir.resources==8.3.0"]

mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("image/svg+xml", ".svg")


def compilar_frontend() -> None:
    subprocess.run(["npm", "run", "build"], cwd=FRONTEND, check=True)


def data_uri(ruta: Path) -> str:
    tipo = mimetypes.guess_type(ruta.name)[0] or "application/octet-stream"
    return f"data:{tipo};base64,{base64.b64encode(ruta.read_bytes()).decode()}"


def incrustar_assets(texto: str) -> str:
    """Cambia cada /assets/archivo por su data URI (fuentes en el CSS, SVG en el JS)."""
    return re.sub(
        r"/assets/([\w.-]+\.(?:woff2|svg|png|jpg|webp))",
        lambda m: data_uri(DIST / "assets" / m.group(1)),
        texto,
    )


def seguro_en_script(texto: str) -> str:
    """Evita que un '</script' dentro del código cierre la etiqueta antes de tiempo."""
    return texto.replace("</script", "<\\/script")


def fuentes_python() -> dict[str, str]:
    archivos = {
        str(p.relative_to(BACKEND_APP.parent)): p.read_text(encoding="utf-8")
        for p in sorted(BACKEND_APP.rglob("*.py"))
        if "__pycache__" not in p.parts
    }
    for p in sorted(NAVEGADOR.glob("*.py")):
        archivos[p.name] = p.read_text(encoding="utf-8")
    return archivos


ARRANQUE = """
<script src="%(pyodide)spyodide.js"></script>
<script>
// Hilo Clínico sin servidor: el backend de Python corre aquí mismo con Pyodide.
// Toda llamada fetch('/api/...') se atiende con app/api/rutas.py (ver scripts/navegador/).
(function () {
  const FUENTES = JSON.parse(document.getElementById('hc-python').textContent);
  const aviso = (texto, error) => {
    const el = document.getElementById('hc-carga');
    if (!el) return;
    el.querySelector('p').textContent = texto;
    if (error) el.classList.add('is-error');
  };

  const listo = (async () => {
    aviso('Descargando Python (Pyodide)…');
    const py = await loadPyodide({ indexURL: %(pyodide_json)s });
    aviso('Instalando pydantic y fhir.resources…');
    await py.loadPackage(%(paquetes_pyodide)s);
    await py.pyimport('micropip').install(%(paquetes_pypi)s);
    aviso('Cargando el backend de Hilo Clínico…');
    const base = '/home/pyodide/hc';
    for (const [ruta, codigo] of Object.entries(FUENTES)) {
      const partes = (base + '/' + ruta).split('/');
      for (let i = 2; i < partes.length; i++) {
        const dir = partes.slice(0, i).join('/');
        if (!py.FS.analyzePath(dir).exists) py.FS.mkdir(dir);
      }
      py.FS.writeFile(base + '/' + ruta, codigo);
    }
    py.runPython(`import sys; sys.path.insert(0, '${base}')`);
    const atender = py.pyimport('despachador').atender_json;
    document.getElementById('hc-carga')?.remove();
    return atender;
  })();
  listo.catch((e) => {
    console.error(e);
    aviso('No se pudo cargar el motor en el navegador. latest.html necesita internet la primera vez (Pyodide y PyPI).', true);
  });

  const fetchOriginal = window.fetch.bind(window);
  window.fetch = async (entrada, opciones = {}) => {
    const url = new URL(typeof entrada === 'string' ? entrada : entrada.url, location.href);
    if (!url.pathname.startsWith('/api/')) return fetchOriginal(entrada, opciones);
    const atender = await listo;
    const metodo = (opciones.method || 'GET').toUpperCase();
    const [status, cuerpo] = JSON.parse(atender(metodo, url.pathname, opciones.body ?? null));
    return new Response(status === 204 ? null : cuerpo, {
      status,
      headers: { 'Content-Type': 'application/json' },
    });
  };
})();
</script>
"""

CARGA = """
<div id="hc-carga" role="status" aria-live="polite">
  <div><strong>Hilo Clínico</strong><p>Preparando…</p>
  <small>El backend de Python corre en tu navegador. La primera carga tarda unos segundos.</small></div>
</div>
<style>
#hc-carga { position: fixed; inset: 0; z-index: 9999; display: grid; place-items: center;
  background: var(--paper, #fbf8f3); color: var(--ink, #1d1b2e); font-family: var(--body, system-ui, sans-serif); }
#hc-carga div { max-width: 26rem; padding: 24px; text-align: center; }
#hc-carga strong { font-family: var(--display, Georgia, serif); font-size: 28px; }
#hc-carga p { font-weight: 700; margin: 12px 0 6px; }
#hc-carga small { color: var(--ink-soft, #5b5870); }
#hc-carga.is-error p { color: var(--coral-deep, #b4402a); }
</style>
"""


def generar() -> Path:
    indice = (DIST / "index.html").read_text(encoding="utf-8")
    js_ruta = re.search(r'<script type="module" crossorigin src="/assets/([^"]+)"></script>', indice)
    css_ruta = re.search(r'<link rel="stylesheet" crossorigin href="/assets/([^"]+)">', indice)
    js = incrustar_assets((DIST / "assets" / js_ruta.group(1)).read_text(encoding="utf-8"))
    css = incrustar_assets((DIST / "assets" / css_ruta.group(1)).read_text(encoding="utf-8"))
    python = json.dumps(fuentes_python(), ensure_ascii=False).replace("</", "<\\/")

    arranque = ARRANQUE % {
        "pyodide": PYODIDE,
        "pyodide_json": json.dumps(PYODIDE),
        "paquetes_pyodide": json.dumps(PAQUETES_PYODIDE),
        "paquetes_pypi": json.dumps(PAQUETES_PYPI),
    }
    html = indice
    html = html.replace('<html lang="en">', '<html lang="es">')
    html = html.replace("<title>frontend</title>", "<title>Hilo Clínico</title>")
    html = re.sub(r'\s*<link rel="icon"[^>]*>', "", html)
    html = html.replace(css_ruta.group(0), f"<style>\n{css}\n</style>")
    html = html.replace(
        js_ruta.group(0),
        f'<script type="application/json" id="hc-python">{python}</script>\n{arranque}',
    )
    html = html.replace(
        '<div id="root"></div>',
        f'{CARGA}<div id="root"></div>\n<script type="module">\n{seguro_en_script(js)}\n</script>',
    )
    SALIDA.write_text(html, encoding="utf-8")
    return SALIDA


if __name__ == "__main__":
    if "--sin-build" not in sys.argv:
        compilar_frontend()
    ruta = generar()
    print(f"{ruta.relative_to(RAIZ)}: {ruta.stat().st_size / 1024:.0f} KB")
