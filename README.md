# Hilo Clínico

Capa de interoperabilidad clínica que une, en una sola historia, los datos de una persona que hoy están repartidos entre su **EPS**, las **IPS** donde la han atendido y los **laboratorios**. Hilo Clínico **no reemplaza** esos sistemas. Los consulta vía **HL7 FHIR R4**, solo con el permiso de la paciente, y deja todo registrado en la auditoría.

> Este repositorio reconstruye como software el prototipo del MVP (`boceto.html`), que es la fuente de verdad funcional. Todos los datos son ficticios.

---

## Proceso TO-BE (BPMN)

![Proceso TO-BE de Hilo Clínico en BPMN](assets/bpmn.png)

Fuente editable: [`assets/hilo-clinico-to-be (1).bpmn`](<assets/hilo-clinico-to-be (1).bpmn>)

**Carriles**

| Carril | Rol |
|---|---|
| Médico de urgencias | Busca a la paciente, revisa su historia y la atiende |
| Hilo Clínico | Índice maestro, consentimiento, adaptadores FHIR, auditoría y RDA |
| Paciente | Autoriza o rechaza el acceso desde su app |
| Sistemas de la red (pool externo) | EPS, IPS y laboratorios que responden las consultas FHIR |
| IHCE del Ministerio de Salud (pool externo) | Recibe el Resumen Digital de Atención (RDA) |

**Recorrido**

1. **Llega a urgencias** (inicio).
2. **Buscar paciente por documento** *(tarea de usuario, médico)*. El médico escribe el documento en el visor y marca si es una urgencia vital.
3. **Identificar en índice maestro** *(servicio)*. El MPI reconoce a la misma persona en la EPS, la IPS y el laboratorio, aunque cada uno la guarde con otro formato.
4. **¿Urgencia vital?** *(compuerta XOR)*
   - **Sí** → **Abrir acceso de emergencia**: acceso sin autorización previa, limitado a 24 horas. La paciente recibe el aviso y el acceso queda auditado.
   - **No** → **Pedir permiso a la paciente** *(envío de mensaje)*. El gestor de consentimiento envía la solicitud a la app.
5. **Responder solicitud en la app** *(tarea de usuario, paciente)*. Decide qué categorías puede ver el médico.
6. **¿Autoriza?** *(XOR)*
   - **No** → **Acceso denegado** (fin). No se consulta ninguna fuente. El médico atiende con lo que la paciente le cuente y el rechazo queda en la auditoría.
   - **Sí** → se une con la rama de emergencia.
7. **Traer y unir datos vía FHIR** *(servicio)*. Los adaptadores consultan cada fuente (*Consulta FHIR → Recursos*) y traducen su formato a recursos FHIR.
8. **Revisar historia y atender** *(tarea de usuario, médico)*. Alergias, consultas, fórmulas, autorizaciones y exámenes aparecen en una sola línea de tiempo.
9. **¿Dónde se registra?** *(XOR, según lo que elija el médico o la configuración de la IPS)*
   - **Hilo Clínico** → **Guardar en Hilo Clínico**.
   - **IPS** → **Enviar atención vía FHIR a la IPS**: `POST` de un `Bundle` de tipo `transaction` al endpoint de la IPS (*Bundle FHIR → 201 Created*). Hilo Clínico guarda solo la referencia.
10. **Auditar y enviar RDA** *(servicio)*. Registra el acceso y envía el Resumen Digital de Atención al IHCE.
11. **Atención registrada** (fin).

---

## Lógica del sistema

### 1. Fuentes de datos (cada una en su formato nativo)

| Fuente | Tipo | Formato | Qué aporta | Recursos FHIR que produce |
|---|---|---|---|---|
| EPS Andina | EPS | Tabla plana (`num_doc`, `fec_nac` `AAAAMMDD`, `regimen`, `estado`) | Afiliación y autorizaciones | `Coverage`, `ServiceRequest` |
| Centro Médico Chapinero | IPS | JSON propio (`id` `P-00417`, documento `CC-1.032.456.789`, fechas `DD/MM/AAAA`) | Alergias, atenciones con CIE-10, fórmulas | `AllergyIntolerance`, `Encounter`, `Condition`, `MedicationRequest` |
| Laboratorio Bioandes | Laboratorio | CSV con `;` (`orden;doc_paciente;fecha_hora;analito;valor;unidad;ref_min;ref_max`) | Hemograma y proteína C reactiva | `Observation` (categoría `laboratory`, con interpretación según el rango de referencia) |

Cada fuente tiene un **adaptador** que lee su formato y devuelve recursos FHIR R4 que apuntan a `Patient/{id maestro}`.

### 2. Índice maestro de pacientes (MPI)

- Normaliza el documento dejando solo los dígitos (`CC-1.032.456.789` → `1032456789`).
- Si el documento tiene menos de 6 dígitos devuelve el error `corto`. Si ninguna fuente lo reconoce devuelve `no-existe`.
- Busca el documento en las tres fuentes y devuelve:
  - **paciente maestro**: `id = hc-{documento}`, nombre normalizado, fecha de nacimiento en ISO y sexo. Marca `complete` cuando las tres fuentes la reconocen.
  - **identidades**: el ID local con que cada fuente conoce a la persona (`CC 1032456789` en la EPS, `P-00417` en la IPS, la orden `LB-2291` en el laboratorio).

### 3. Gestor de consentimiento

La paciente autoriza por **categorías**. Cada categoría habilita ciertos tipos de recurso:

| Categoría | Tipos de recurso habilitados |
|---|---|
| Alergias y medicamentos | `AllergyIntolerance`, `MedicationRequest` |
| Exámenes de laboratorio | `Observation` |
| Consultas anteriores | `Encounter`, `Condition` |
| Afiliación y autorizaciones de tu EPS | `Coverage`, `ServiceRequest` |

- Cada decisión genera un recurso `Consent` (`provision.type = permit`) con vigencia de **24 horas**, a favor del médico y de su IPS.
- **Modo paciente**: ella elige qué categorías comparte.
- **Modo emergencia**: se abren todas las categorías sin autorización previa y la paciente recibe el aviso.
- **Revocación**: desde la app la paciente puede revocar el acceso en cualquier momento. Desde ese momento la historia deja de estar visible para el médico.
- **Regla central**: un tipo de recurso solo se consulta si hay un `Consent` activo que lo incluye. Si no, la petición responde **403** y **no se consulta la fuente**.

### 4. Consulta y unión vía FHIR

Por cada fuente y cada tipo de recurso se arma una petición (`GET /Observation?patient=…&category=laboratory`, `GET /Coverage?beneficiary=…`, etc.) y se registra en el log de **Peticiones FHIR** con su estado (200 o 403) y el número de recursos devueltos.

Con los recursos permitidos se construye la **línea de tiempo**, ordenada de lo más reciente a lo más antiguo, con fecha relativa ("hace 8 días"):

- Exámenes de laboratorio, con la bandera de cada analito y marca de *reciente* si tienen 30 días o menos.
- Consultas (`Encounter` con su `Condition`, CIE-10 y profesional).
- Fórmulas médicas (`MedicationRequest`).
- Autorizaciones de la EPS (`ServiceRequest` aprobada y aún sin realizar).

Aparte, en un lugar destacado, se muestran las **alergias** (con criticidad) y la **cobertura** de la EPS.

### 5. Registro de la atención

- El médico escribe la nota de la atención (por ejemplo: *"No se repiten hemograma ni PCR"*, porque ya están en la historia).
- **RDA**: un `Bundle` de tipo `document` con `Composition`, `Encounter` (clase `EMER`), la alergia relevante y `ClinicalImpression` con la nota.
- **Envío a la IPS**: un `Bundle` de tipo `transaction` con `Encounter`, `ClinicalImpression` y `Provenance` (origen: Hilo Clínico) que se envía por `POST` al endpoint FHIR de la IPS. Se espera `201 Created`.

### 6. Auditoría

Cada paso deja un `AuditEvent` con quién hizo qué, sobre qué fuente, el resultado (`ok`, `warn` o `deny`) y la hora. Esto incluye la búsqueda en el MPI, la apertura de emergencia, la solicitud de permiso, la respuesta de la paciente, cada consulta a una fuente (o su bloqueo), el guardado o envío de la atención, el envío del RDA y la revocación.

### 7. Motor del proceso

El proceso es una **máquina de estados** que recorre el modelo BPMN nodo por nodo:

- Las **tareas de usuario** (`user`) se detienen y esperan una acción del médico o de la paciente.
- Las **tareas de servicio** (`service`, `send`) y las **compuertas** (`xor`) avanzan solas y ejecutan su efecto: MPI, consentimiento, FHIR, auditoría o RDA.
- Las compuertas eligen su salida a partir del contexto: si se marcó urgencia vital, si la paciente autorizó y qué destino eligió el médico.
- La simulación se puede **avanzar o retroceder paso a paso** (flechas ← →) y **reiniciar** en cualquier escenario.

---

## Escenarios de la simulación

Paciente de ejemplo: **Mariana Sofía López Castro**, CC 1.032.456.789. Llega a urgencias de la **Clínica del Pacífico (Cali)** con dolor abdominal y fiebre. La atiende el **Dr. Mateo Vargas**.

| Escenario | Qué pasa |
|---|---|
| **Con autorización** | Mariana autoriza desde su app. Se consultan solo las categorías que eligió. |
| **Urgencia vital** | Mariana no puede responder. Se abre el acceso de emergencia por 24 h y se audita. |
| **Mariana no autoriza** | Sin permiso no se consulta nada. El proceso termina en *Acceso denegado*. |

Lo que gana la atención: el médico ve a tiempo la **alergia grave a la penicilina** y los **exámenes del 7 de noviembre**, así que no repite el hemograma ni la PCR.

### Más casos de ejemplo

Además de Mariana y Jorge hay **cinco pacientes más**, cada uno atendido por un médico de urgencias de una clínica distinta de la red. El médico se elige en la cabecera (**Atiende**) o con `medico` al crear la simulación. Cédulas, clínicas, médicos y qué muestra cada caso: **[CASOS.md](CASOS.md)**.

| Cédula | Paciente | Clínica | Médico |
|---|---|---|---|
| 1032456789 | Mariana Sofía López Castro | Clínica del Pacífico (Cali) | Dr. Mateo Vargas |
| 79845120 | Jorge Eliecer Pardo Ruiz | Clínica del Pacífico (Cali) | Dr. Mateo Vargas |
| 1017234567 | Carlos Andrés Gómez Restrepo | Fundación Santa Fe de Bogotá | Dra. Catalina Ríos |
| 52987654 | Luisa Fernanda Rojas Herrera | Centro Médico Chapinero | Dr. Julián Ortega |
| 1144056789 | Andrés Felipe Martínez Ospina | Hospital Simón Bolívar | Dr. Sebastián Mejía |
| 1000345678 | Valentina Ruiz Quintero | Clínica de Marly | Dra. Natalia Herrera |
| 19456321 | Héctor Julio Cárdenas Pinzón | Fundación Clínica Cardioinfantil | Dra. Paula Cifuentes |

---

## Vistas del prototipo

- **Simulación**: el visor clínico del médico y la app de la paciente lado a lado, más el panel *La capa por dentro* con sus pestañas: Peticiones FHIR, Auditoría, Recurso FHIR y Red de IPS.
- **Proceso BPMN**: el diagrama TO-BE, con la ejecución resaltada paso a paso y una ayuda en cada nodo.
- **Impacto en salud**: el proceso de hoy frente al proceso con Hilo Clínico, por qué esperamos impacto en salud y el aporte a los Objetivos de Desarrollo Sostenible.

---

## Stack propuesto

**Toda la lógica vive en el backend (Python).** El frontend solo pinta las pantallas y llama a la API. Así, lo que se explica y se defiende (identificar a la paciente, pedir permiso, traducir a FHIR, auditar) está en un solo lugar y en un lenguaje que el equipo domina.

### Backend: el núcleo

| Capa | Tecnología | Por qué |
|---|---|---|
| Lenguaje | **Python 3.11+** | El lenguaje que domina el equipo |
| API | **FastAPI** + **Uvicorn** | Rápida de escribir, valida datos y genera documentación en `/docs` |
| Recursos FHIR R4 | **fhir.resources** | Valida que `Consent`, `AuditEvent`, `Bundle`, etc. sean FHIR válido |
| Tests | **pytest** + **httpx** (`TestClient`) | Tests unitarios de cada módulo y tests de la API |
| Persistencia (fase posterior) | **SQLite → PostgreSQL** | Consentimientos, auditoría e índice maestro. En el MVP basta con memoria |
| Fuentes de la red (fase posterior) | **HAPI FHIR** en Docker | Servidores FHIR reales que hacen de EPS, IPS y laboratorio |

### Frontend: solo interfaz, idéntica al boceto

| Capa | Tecnología | Por qué |
|---|---|---|
| UI | **React + TypeScript + Vite** | El boceto está hecho en React, así se reproduce igual |
| Estilos | **El CSS del boceto** (mismos tokens: `--ink`, `--coral`, `--sky`…) | Los mismos colores, tipografías y estructura |
| Animaciones e iconos | **Framer Motion**, **lucide-react** | Las mismas librerías del boceto |
| Conexión con el backend | `fetch` a `/api/...` (proxy de Vite al puerto 8000) | El front no toma decisiones: pide y muestra |

### Cómo se reparte la lógica en el backend

```
backend/app/
  actores.py  el médico de urgencias y su IPS (datos ficticios)
  sources/    fuentes simuladas en su formato nativo: eps.py (tabla), ips.py (JSON), lab.py (CSV)
  mpi/        índice maestro: normalizar_documento(), buscar() → PacienteMaestro + identidades
  adapters/   eps.py, ips.py, lab.py: cada fuente → recursos FHIR R4 validados con fhir.resources
  consent/    categorias.py (qué habilita cada categoría), gestor.py (crear, permite, revocar),
              consulta.py (consultar_red: 200 si hay permiso, 403 si no, sin tocar la fuente)
  audit/      registro.py: EventoAuditoria (quién, qué, detalle, resultado, hora) → AuditEvent FHIR
  fhir/       rda.py (Bundle document), envio.py (Bundle transaction + Provenance),
              linea_tiempo.py (lo que ve el médico), red.py (endpoints FHIR de la red de IPS)
  process/    modelo.py (18 nodos, 3 carriles, 2 pools, 19 flujos, compuertas en siguiente()),
              motor.py (máquina de estados: actuar / completar / llegar / paso / correr / revocar)
  api/        rutas.py (endpoints), esquemas.py (cuerpos y serialización a JSON),
              almacen.py (simulaciones en memoria + historial para el paso atrás)
  main.py     punto de entrada
backend/tests/
  test_sources.py  test_mpi.py  test_adapters.py  test_consent.py  test_audit.py
  test_fhir.py  test_linea_tiempo.py  test_process.py  test_api.py  test_health.py
```

### Endpoints

| Método y ruta | Qué hace |
|---|---|
| `GET /api/proceso` | Modelo BPMN (carriles, pools, nodos con coordenadas y ayuda, flujos, mensajes, escenarios) |
| `GET /api/catalogo` | Fuentes de la red, categorías de consentimiento, médico de turno, `medicos`, `casos` y red de IPS |
| `POST /api/simulaciones` | Crea una simulación `{escenario, inicio?, medico?}` → estado completo (incluye `medico`); médico desconocido → 422 |
| `GET /api/simulaciones/{id}` | Estado completo: nodo, estado, visitados, flujos y `ctx` (MPI, consent, log, recursos, línea de tiempo, RDA, envío, auditoría) |
| `POST /api/simulaciones/{id}/paso` | Hace la transición que toque |
| `POST /api/simulaciones/{id}/actuar` | El médico o la paciente actúan: `{documento, emergencia}` · `{decision, categorias}` · `{nota, destino}` |
| `PATCH /api/simulaciones/{id}/borrador` | Cambia lo escrito en pantalla sin mover el proceso |
| `POST /api/simulaciones/{id}/revocar` | La paciente revoca el acceso |
| `POST /api/simulaciones/{id}/atras` | Vuelve al estado anterior |
| `DELETE /api/simulaciones/{id}` | Borra la simulación |

Los recursos FHIR viajan como JSON estándar (`resourceType`, …), así que el panel "Recurso FHIR" del frontend los muestra tal cual. La documentación interactiva está en `http://localhost:8000/docs`.

### Estados del motor

| Estado | Significa | Sale con |
|---|---|---|
| `waiting` | En una tarea de usuario (`t_buscar`, `t_resp`, `t_atender`) | `actuar(sim, **datos)` |
| `running` | En una tarea de servicio o compuerta; su efecto ya se ejecutó | `completar(sim)` |
| `moving` | El token va por un flujo (el frontend lo anima) | `llegar(sim)` |
| `ended` | En `end_ok` o `end_no` | — |

`paso(sim)` hace la transición que toque (en `waiting` usa la respuesta del escenario) y `correr(escenario)` recorre el proceso completo. El reloj de la simulación avanza unos segundos por nodo, así la auditoría y los `Consent` tienen horas coherentes sin depender del reloj real.

Cada módulo se construyó con TDD: primero sus tests en `backend/tests/`, luego el código mínimo que los pone en verde.

Las dependencias van en un solo sentido: `api → process → (mpi, consent, adapters, audit) → (sources, fhir)`. Ningún módulo de lógica depende de FastAPI, así que se prueban con pytest sin levantar el servidor.

---

## Estructura del repositorio

```
assets/      diagrama BPMN (PNG y .bpmn editable)
backend/     API en Python (FastAPI): toda la lógica + tests
frontend/    interfaz en React (réplica visual del boceto)
boceto.html  prototipo de referencia (fuente de verdad funcional y visual)
```

## Cómo ejecutar

**Backend** (puerto 8000):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload     # API en http://localhost:8000/docs
pytest                            # tests
```

**Frontend** (puerto 5173, en otra terminal):

```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```
