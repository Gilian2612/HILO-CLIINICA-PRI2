# CLAUDE.md — Hilo Clínico

Guía para trabajar en este repositorio. Léela completa antes de tocar código.

## 1. Qué es el proyecto

**Hilo Clínico** es una capa de interoperabilidad clínica (Colombia) que une, en una sola historia, los datos de una persona repartidos entre su **EPS**, las **IPS** y los **laboratorios**. Consulta esos sistemas vía **HL7 FHIR R4**, solo con permiso de la paciente, y deja todo en auditoría. No reemplaza los sistemas existentes.

Caso de uso del MVP: **Mariana Sofía López Castro** (CC 1.032.456.789) llega a urgencias de la **Clínica del Pacífico (Cali)** con dolor abdominal y fiebre. La atiende el **Dr. Mateo Vargas**. Gracias a Hilo Clínico, el médico ve su alergia grave a la penicilina y los exámenes del 7 de noviembre, y no repite el hemograma ni la PCR.

Todos los datos son ficticios.

## 2. Fuente de verdad: `boceto.html`

`boceto.html` (~800 KB) es el prototipo original y la **fuente de verdad funcional y visual**. Es una app React compilada y minificada en un solo archivo, con React, framer-motion, lucide y las fuentes Urbanist/Fraunces incrustadas en base64.

Cómo leerlo cuando haga falta:
- Las líneas 1–21 son React/ReactDOM minificado: ignorar.
- Las **líneas 22–27** contienen el código propio de la app (datos, lógica, componentes). Los caracteres acentuados están como `\xE9`; decodificar con `re.sub(r'\\x([0-9A-F]{2})', ...)`.
- La línea 28 en adelante hasta ~521 es el **CSS** (variables `--ink`, `--coral`, `--sky`, etc. en `:root`, luego estilos por componente).
- La línea 522 son las fuentes en base64; la 523 los `@font-face`.
- Las variables `__hcRed`, `__hcEP`, `__hcWB`, `__hcSnap`, `__hcEn` al inicio del `<script>` fueron agregadas a mano después de compilar (red de IPS, envío a la IPS, historial para deshacer). Ya están portadas al backend.
- Nombres minificados útiles: `Re` (fuentes), `Ce` (médico), `D4` (EPS), `qs` (IPS), `xL` (CSV lab), `yp` (MPI), `vL/SL/IL` (adaptadores), `_s` (categorías), `E4` (Consent), `Sp` (consulta a la red), `wp` (línea de tiempo), `kp` (auditoría), `Pp` (RDA), `Dn` (nodos BPMN), `wo` (flujos), `H1` (mensajes), `G1` (compuertas), `EL` (efectos por nodo), `RL` (acciones de usuario), `En` (reducer), `cy` (componente raíz), `Up` (CSS).

El boceto tenía defectos FHIR que **ya se corrigieron en el backend** y no deben reintroducirse:
- `Consent.provision.period.end` era la cadena `"P24H"`; ahora es `inicio + 24h`.
- `Consent` llevaba campos inventados `_mode` y `_scope`.
- `AuditEvent` tenía `who`, `action` y `detail` como texto libre; ahora es R4 válido.
- `AllergyIntolerance.reaction` no tenía `manifestation` (obligatorio).
- `Observation.effectiveDateTime` venía como `2026-11-07T08:12` (sin segundos ni zona); el adaptador lo normaliza a `2026-11-07T08:12:00-05:00`.

## 3. Decisiones de arquitectura (no re-discutir)

1. **Toda la lógica vive en el backend, en Python.** El usuario domina Python y Java, no JavaScript/TypeScript. Lo que se explica y se defiende (MPI, consentimiento, adaptadores, motor del proceso) tiene que estar en Python.
2. **El frontend es React + TypeScript, pero delgado**: solo pinta pantallas y llama a la API. No toma decisiones de negocio. Debe quedar **idéntico al boceto** (mismos colores, tipografías, estructura y animaciones).
3. **Se eligió Python (FastAPI) sobre Java** por velocidad para un MVP y por `fhir.resources`. Java/HAPI queda como alternativa futura si hace falta un servidor FHIR propio.
4. **FHIR validado en compilación/ejecución** con `fhir.resources` (R4B). Nunca armar recursos FHIR como dicts sueltos; siempre instanciar la clase (`Coverage(...)`, `Bundle(...)`) para que valide.
5. **Las funciones reciben `ahora: datetime` como parámetro**, nunca leen el reloj. Así los tests son deterministas y el motor simula el paso del tiempo.
6. **TDD obligatorio**: primero los tests en `backend/tests/`, correrlos para ver el rojo, luego el código mínimo. Cada módulo nuevo lleva su `test_*.py`.
7. **Nombres en español** en código, tests, docstrings y commits (`buscar`, `crear_consentimiento`, `linea_de_tiempo`). Los nombres FHIR se mantienen en inglés (`Consent`, `resourceType`).
8. Estado en memoria por ahora (`app/api/almacen.py`). La persistencia (SQLite → PostgreSQL) es fase posterior.

## 4. Estructura del repo

```
HILO-CLIINICA-PRI2/
├── CLAUDE.md               esta guía
├── README.md               documentación para humanos (lógica, BPMN, stack, endpoints)
├── boceto.html             prototipo original (fuente de verdad)
├── assets/
│   ├── bpmn.png            diagrama del proceso TO-BE
│   └── hilo-clinico-to-be (1).bpmn   fuente editable del diagrama
├── backend/                Python 3.11+ · FastAPI · fhir.resources · pytest
│   ├── pyproject.toml
│   ├── .venv/              (ignorado) crear con python3 -m venv .venv
│   ├── app/
│   │   ├── main.py         FastAPI app; incluye router y /api/health
│   │   ├── actores.py      MEDICO (Profesional: Dr. Mateo Vargas, Clínica del Pacífico, Cali)
│   │   ├── sources/        fuentes en formato nativo
│   │   │   ├── __init__.py FUENTES dict: eps, ips, lab (Fuente: id, tipo, nombre, ciudad, formato, color)
│   │   │   ├── eps.py      AFILIADOS, AUTORIZACIONES (tabla plana, fechas AAAAMMDD) · afiliados(), autorizaciones()
│   │   │   ├── ips.py      DATOS (JSON: pacientes, alergias, atenciones, formulas; fechas DD/MM/AAAA) · datos()
│   │   │   └── lab.py      CSV (string con ;) · filas()
│   │   ├── mpi/
│   │   │   └── indice.py   normalizar_documento(), buscar() → ResultadoBusqueda(paciente: PacienteMaestro, identidades: list[Identidad])
│   │   │                   excepciones: DocumentoCorto (<6 dígitos), PacienteNoEncontrado
│   │   ├── adapters/
│   │   │   ├── __init__.py ADAPTADORES dict: Adaptador(fuente, tipos, a_fhir)
│   │   │   ├── _comun.py   referencia_paciente(), de_aaaammdd(), de_ddmmaaaa(), de_fecha_hora_local()
│   │   │   ├── eps.py      a_fhir() → [Coverage, ServiceRequest...]
│   │   │   ├── ips.py      a_fhir() → [AllergyIntolerance, Encounter+Condition (por atención), MedicationRequest]
│   │   │   └── lab.py      a_fhir() → [Observation...] con interpretación H/L/N
│   │   ├── consent/
│   │   │   ├── categorias.py  CATEGORIAS (alergias, laboratorios, consultas, eps), TODAS, tipos_de()
│   │   │   ├── gestor.py      crear_consentimiento(paciente, categorias, modo, ahora) → Consent · permite(consent, tipo, ahora) · revocar(consent)
│   │   │   └── consulta.py    consultar_red(paciente, consent, ahora) → ResultadoConsulta(log: [Peticion], recursos)
│   │   ├── audit/
│   │   │   └── registro.py registrar(hora, quien, accion, detalle, resultado) → EventoAuditoria · .a_fhir() → AuditEvent
│   │   ├── fhir/
│   │   │   ├── rda.py          crear_rda(paciente, nota, ahora, recursos) → Bundle document
│   │   │   ├── envio.py        crear_envio_ips(rda, ahora) → Bundle transaction (Encounter, ClinicalImpression, Provenance)
│   │   │   ├── linea_tiempo.py linea_de_tiempo(recursos, hoy) → LineaTiempo(items, alergias, cobertura) · etiqueta_fecha() · hace()
│   │   │   └── red.py          ENDPOINT_IPS, RED_IPS (6 IPS con endpoint FHIR)
│   │   ├── process/
│   │   │   ├── modelo.py   NODOS (18), CARRILES (3), POOLS (2), FLUJOS (19), MENSAJES (5), flujo_entre(), siguiente()
│   │   │   └── motor.py    Simulacion, Contexto, Borrador, ESCENARIOS · nueva_simulacion(), actuar(), completar(), llegar(), paso(), correr(), revocar_acceso()
│   │   └── api/
│   │       ├── rutas.py    router con prefijo /api
│   │       ├── esquemas.py CrearSimulacion, Accion, CambioBorrador · serializar_simulacion(), fhir_json()
│   │       └── almacen.py  Almacen en memoria con historial (mutar, atras) · instancia global `almacen`
│   └── tests/              92 tests · pytest
│       test_sources.py test_mpi.py test_adapters.py test_consent.py test_audit.py
│       test_fhir.py test_linea_tiempo.py test_process.py test_api.py test_health.py
└── frontend/               React 19 + TypeScript + Vite (esqueleto, aún sin las vistas)
    ├── vite.config.ts      proxy /api → http://localhost:8000
    └── src/
        ├── main.tsx
        ├── App.tsx         placeholder: muestra el estado de /api/health
        └── index.css       mínimo
```

## 5. Cómo ejecutar y probar

```bash
# Backend (puerto 8000)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                       # 92 tests, ~2 s
uvicorn app.main:app --reload   # http://localhost:8000/docs

# Frontend (puerto 5173, otra terminal)
cd frontend
npm install
npm run dev
```

Desde la raíz, sin activar el venv: `cd backend && .venv/bin/pytest -q`.

## 6. Lo que está hecho (pasos 1–7, backend completo)

### Paso 1 · `sources/` — fuentes en formato nativo
Datos del boceto tal cual. Tres formatos distintos a propósito: tabla plana (EPS), JSON propio (IPS), CSV con `;` (lab). Las funciones devuelven copias.

### Paso 2 · `mpi/` — índice maestro
- `normalizar_documento("CC-1.032.456.789") == "1032456789"`.
- `buscar()` arma `PacienteMaestro(id="hc-{doc}", documento, documento_label="CC 1.032.456.789", nombre, nombres, fecha_nacimiento ISO, sexo "female"/"male", completo)` y la lista de `Identidad(fuente, id_local, como, nacimiento)`. Prefiere la IPS para el nombre (tiene tildes) y la EPS para la fecha.
- Segundo paciente: **Jorge Eliecer Pardo Ruiz** (CC 79845120), solo en la EPS, `completo=False`.

### Paso 3 · `adapters/` — nativo → FHIR R4
Todos los recursos apuntan a `Patient/hc-{doc}` (nunca al ID local de la fuente). IDs: `cov-{doc}`, `AUT-88231`, `alg-P-00417-1`, `enc-P-00417-N`, `cond-P-00417-N`, `med-P-00417-1`, `obs-LB-2291-N`. Mariana produce **12 recursos**: 1 Coverage, 1 ServiceRequest, 1 AllergyIntolerance, 2 Encounter, 2 Condition, 1 MedicationRequest, 4 Observation.

### Paso 4 · `consent/` — gestor de consentimiento
- Categorías → tipos: alergias → AllergyIntolerance, MedicationRequest · laboratorios → Observation · consultas → Encounter, Condition · eps → Coverage, ServiceRequest.
- `crear_consentimiento(..., modo="paciente"|"emergencia", ahora)`: Consent R4 válido, `id="consent-{doc}-{modo}"`, vigencia 24 h, `provision.class` con los tipos, actor = `MEDICO.display`.
- `permite()` es la **regla central**: activo + vigente + tipo incluido. `revocar()` devuelve copia con `status="inactive"`.
- `consultar_red()`: por cada adaptador y tipo arma una `Peticion(fuente, tipo, metodo, url, status, cantidad)`; 200 si permitido, 403 si no (y **no llama al adaptador**). URLs: `/Coverage?beneficiary=…`, `/Observation?patient=…&category=laboratory`, `/{Tipo}?patient=…`.

### Paso 5 · `audit/` y `fhir/`
- `EventoAuditoria(id, hora, quien, accion, detalle, resultado "ok"|"warn"|"deny")`; id determinista `aud-HHMMSS-{hash31 % 997}`. `a_fhir()` → AuditEvent con `outcome` "0"/"4" y `outcomeDesc` = resultado.
- RDA: `Bundle document` con Composition, Encounter (EMER, motivo "Dolor abdominal y fiebre"), AllergyIntolerance si existe, ClinicalImpression con la nota. `id="rda-{doc}-{12 dígitos del timestamp}"`.
- Envío a IPS: `Bundle transaction`, `id="envio-{14 dígitos}"`, entradas con `request.method="POST"` y `fullUrl="urn:uuid:…"`; la ClinicalImpression referencia al Encounter por su urn; Provenance con agente "Hilo Clínico (capa de interoperabilidad)".
- Línea de tiempo: `Item(tipo "laboratorio"|"consulta"|"formula"|"autorizacion", fuente, titulo, subtitulo, detalle, recursos, fecha_label "7 nov 2026", hace "hace 7 días", reciente ≤30 días, analitos)`. El laboratorio es un solo item. Orden: más reciente primero, empates conservan orden de inserción (lab, encounters, meds, autorizaciones).

### Paso 6 · `process/` — motor BPMN
- Nodos (`kind`: start, end, user, service, send, xor) con coordenadas del diagrama original para que el frontend lo dibuje. Tareas de usuario: `t_buscar`, `t_resp`, `t_atender`.
- `siguiente(nodo, *, emergencia, decision, destino)` resuelve las compuertas: `g_urg` → `t_emerg`/`t_solic`; `g_aut` → `g_join`/`end_no`; `g_dest` → `t_envio`/`t_guardar`.
- Estados: `waiting` (tarea de usuario) → `actuar()`; `running` (servicio/compuerta, efecto ya ejecutado) → `completar()`; `moving` (token en un flujo) → `llegar()`; `ended`. `paso()` hace la que toque; en `waiting` usa `_respuesta_del_escenario` (rechazo → denied). `correr(escenario|sim, inicio, hasta=nodo)` avanza hasta el fin o hasta quedar esperando en `hasta`.
- **Importante**: la búsqueda en el MPI ocurre en `actuar()` de `t_buscar` (antes de moverse); la auditoría "Búsqueda en índice maestro" se escribe en `_efecto()` al **llegar** a `t_mpi`. Es el comportamiento del boceto.
- Reloj: `ctx.reloj` en segundos; cada efecto avanza 1–9 s (`_avanzar`). `sim.ahora()` = inicio + reloj. Zona por defecto UTC-5.
- Escenarios: `consentimiento` (recorre t_solic → t_resp → granted), `emergencia` (borrador.emergencia=True → t_emerg), `rechazo` (t_resp → denied → end_no). Las 8 acciones de auditoría del escenario con autorización están en `test_process.py::test_escenario_con_autorizacion`.
- `NOTA_POR_DEFECTO` es la nota clínica del boceto.

### Paso 7 · `api/` — REST
| Método y ruta | Qué hace |
|---|---|
| `GET /api/health` | `{"status":"ok"}` |
| `GET /api/proceso` | carriles, pools, nodos, flujos, mensajes, escenarios |
| `GET /api/catalogo` | fuentes, categorias, medico, red `{endpoint, ips}` |
| `POST /api/simulaciones` `{escenario, inicio?}` | 201 + estado; escenario inválido → 422 |
| `GET /api/simulaciones/{id}` | estado completo (404 si no existe) |
| `POST …/{id}/paso` | transición que toque |
| `POST …/{id}/actuar` `{documento?, emergencia?, decision?, categorias?, nota?, destino?}` | solo se pasan los campos enviados (`exclude_unset`) |
| `PATCH …/{id}/borrador` | edita lo escrito; no mueve el proceso ni entra al historial; si cambia `documento` limpia `error_busqueda` |
| `POST …/{id}/revocar` | revoca el consent |
| `POST …/{id}/atras` | restaura el snapshot anterior conservando el borrador actual |
| `DELETE …/{id}` | 204 |

Forma de la respuesta: `{id, escenario, inicio, ahora, nodo, estado, visitados, flujos, en_movimiento{flujo,desde,hacia}|null, puede_volver, ctx{borrador, error_busqueda, emergencia, mpi{paciente, identidades}, solicitud, decision, consent, revocado, log[], recursos[], linea{items, alergias, cobertura}, nota, destino, rda, envio, auditoria[{id,hora,quien,accion,detalle,resultado}], reloj}}`. Los recursos FHIR van como JSON estándar (`model_dump(mode="json", by_alias=True, exclude_none=True)`).

Historial: `Almacen.mutar()` hace `deepcopy` antes de aplicar la acción y guarda el snapshot solo si la serialización cambió.

## 7. Lo que falta

### Paso 8 · Frontend (siguiente)
Réplica visual del boceto en `frontend/`, consumiendo la API. No hay lógica de negocio en el front. Orden sugerido:

1. **Extraer del boceto** el CSS (línea 28 → ~521 de `boceto.html`: `:root` con tokens, estilos de `.top`, `.views`, `.scenario`, `.visor`, `.phone`, `.hood`, `.bp-*`, etc.) a `frontend/src/styles/`. Instalar fuentes con `@fontsource/urbanist` y `@fontsource/fraunces` en vez de base64. Dependencias: `framer-motion`, `lucide-react`.
2. **Cliente de la API** (`src/api.ts`): funciones `crearSimulacion`, `paso`, `actuar`, `patchBorrador`, `revocar`, `atras`, `getProceso`, `getCatalogo`. Tipos TS que reflejen la respuesta de `GET /api/simulaciones/{id}`.
3. **Shell**: cabecera con wordmark (`z4` en el boceto, SVG con `N4.viewBox`), etiqueta "Prototipo del MVP, con datos ficticios", nav de 3 vistas (Simulación, Proceso BPMN, Impacto en salud) con subrayado animado (`layoutId="view-underline"`), fieldset de escenario (radio buttons; cambiar = crear nueva simulación). Teclas ← → = atrás / paso (el boceto las captura en `window`, salvo en inputs).
4. **Vista Proceso BPMN** (`src/ui/bpmn/`): SVG con `viewBox="8 10 1704 526"`; carriles, pools, nodos por `kind` (rect redondeado para tareas, rombo para xor, círculos para start/end, iconos de usuario/engranaje/sobre), flujos como polilíneas con flecha, mensajes punteados. Resaltar `visitados`, el `nodo` actual y animar el token por `en_movimiento` (framer-motion sobre los `puntos` del flujo, duración ~720 ms). Cada nodo es clicable y muestra su `ayuda`. Panel lateral "Pasos del proceso", leyenda "Convenciones BPMN".
5. **Vista Simulación** (`src/ui/simulation/`): tres zonas.
   - **Visor clínico del médico** (`.visor`): cabecera con org/ciudad, "Visor clínico de urgencias", nombre/rol del médico. En `t_buscar`: formulario "¿A quién vas a atender?" (tipo de documento, número, checkbox urgencia vital) → `actuar({documento, emergencia})`; errores `corto` / `no-existe`. Tras MPI: tarjeta del paciente con identidades unidas. En `t_atender`: alergias destacadas, cobertura, línea de tiempo (items con `fecha_label`, `hace`, badge `reciente`, analitos con bandera), textarea con la nota, selector de destino (Hilo Clínico / IPS) → `actuar({nota, destino})`. Al final: "Resultados de esta atención".
   - **App de la paciente** (`.phone`): teléfono con hora "10:41"; pantallas según estado: inactiva / solicitud pendiente (lista de 4 categorías con checkboxes, botones autorizar / no autorizar → `actuar({decision, categorias})`) / acceso activo (quién, hasta cuándo, botón "Revocar acceso" → `revocar`) / aviso de emergencia / rechazado / revocado. Switch de pantalla "Pantalla: Médico | Paciente" que cambia solo cuando el proceso cambia de carril.
   - **"La capa por dentro"** (`.hood`): 4 pestañas con contador: Peticiones FHIR (`ctx.log`: método, url, status 200/403/201, cantidad, con color por fuente), Auditoría (`ctx.auditoria`), Recurso FHIR (JSON del recurso seleccionado al hacer clic en un item de la línea de tiempo, o el RDA/envío al terminar), Red de IPS (`catalogo.red.ips` con rol y estado). El boceto cambia automáticamente a "fhir" al llegar a `t_fhir` y a "recurso" en `t_cerrar`/`t_envio`.
   - Barra de pasos arriba (`iy` en el boceto) con botones "Paso anterior", "Paso"/"Reiniciar la simulación" y el nombre del nodo actual.
6. **Vista Impacto en salud** (`src/ui/impact/`): contenido estático del boceto: "Hoy, sin Hilo Clínico" vs "Con Hilo Clínico" (comparación del proceso), "Qué cambia para Mariana y para el sistema", "Por qué esperamos impacto en salud", "Aporte a los Objetivos de Desarrollo Sostenible", "Sostenibilidad". Extraer los textos del boceto (buscar `aria-label` y `children:"…"` en las líneas 22–27).
7. **Accesibilidad y detalle**: el boceto ya tiene `aria-label`, `role="tab"`, `aria-pressed`, `prefers-reduced-motion`, enlace "Saltar al contenido". Mantenerlos.
8. Reemplazar el placeholder `App.tsx`; `index.css` pasa a importar los estilos extraídos.

### Después del frontend (opcional, fase 2)
- Persistencia: `Almacen` sobre SQLite y luego PostgreSQL (consentimientos, auditoría, MPI).
- Fuentes reales: servidores HAPI FHIR en Docker como EPS/IPS/lab; los adaptadores pasan de leer `sources/` a hacer `GET` reales.
- Autorización SMART on FHIR (OAuth 2.0).
- `docker compose up` que levante backend + frontend.
- CI con GitHub Actions (pytest + build del frontend).
- Tests e2e con Playwright para los 3 escenarios.

## 8. Convenciones de trabajo

- **Rama**: se trabaja en `develop`; `main` es estable. El usuario hace los commits él mismo: proponer el mensaje, no ejecutar `git commit` salvo que lo pida.
- **Mensajes de commit**: prefijo en mayúsculas `ADD:`, `DOCS:`, `FIX:`, seguido de descripción en español. Ejemplo: `ADD: backend FastAPI con fuentes, MPI, adaptadores FHIR y consentimiento (TDD)`.
- **Idioma**: todo en español (código, comentarios, tests, README, respuestas al usuario).
- **TDD**: tests primero, siempre. Ver rojo, luego verde. Al terminar un módulo, actualizar la sección correspondiente del README.
- **No tocar `boceto.html`** ni `assets/`.
- `.gitignore` ya cubre `.DS_Store`, `node_modules`, `dist`, `.venv`, `*.egg-info`, `.pytest_cache`, `__pycache__`.

## 9. Trampas conocidas

- `fhir.resources` 8.x: importar desde `fhir.resources.R4B.*` (no `R4`, no la raíz que es R5). El atributo `class` se llama `class_fhir` en Python (`Encounter.class_fhir`, `Consent.provision.class_fhir`); al construir con dict se usa la clave `"class"`.
- `fhir.resources` convierte `dateTime` de solo fecha a `datetime.date` y con hora a `datetime` con zona. Para comparar en tests: `str(x) == "2026-11-06"` o `x.isoformat()`.
- Un `dateTime` FHIR con hora **exige segundos y zona**. Usar `de_fecha_hora_local()`.
- `Consent` R4 exige `scope` y `category`; `AuditEvent` exige `type`, `recorded`, `agent[].requestor`, `source.observer`; `Provenance` exige `target`, `recorded`, `agent[].who`; `AllergyIntolerance.reaction[].manifestation` es obligatorio.
- `actuar()` ignora llamadas cuando `estado != "waiting"`; `revocar_acceso()` ignora si no hay consent activo (no duplica auditoría).
- En la API, `Accion.model_dump(exclude_unset=True)`: no pasar `None` a `actuar()` porque usa `payload.get(campo, borrador.campo)`.
- La carpeta `src/` original de la raíz se eliminó; no recrearla. El código va en `backend/app` y `frontend/src`.
- El archivo `assets/hilo-clinico-to-be (1).bpmn` tiene espacio y paréntesis en el nombre; el enlace del README lo contempla.
