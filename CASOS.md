# Casos de ejemplo de Hilo Clínico

Siete pacientes ficticios, seis clínicas de la red y un médico de urgencias por clínica. **Todos los datos son inventados**: las cédulas, los nombres y los médicos no corresponden a personas reales. Los nombres de las clínicas solo se usan como ejemplo de una red de IPS.

Mariana y Jorge vienen del boceto. Los otros cinco se agregaron para mostrar situaciones distintas: pacientes que están en las tres fuentes, en dos o solo en la EPS; alergias graves y leves; varias órdenes de laboratorio; autorizaciones pendientes.

## Cómo usar un caso

1. En el panel de pasos (izquierda), en **Atiende**, elige el médico. La simulación se reinicia con ese médico y su clínica, y el visor trae escrita la cédula de su caso.
2. Elige el **escenario**: con autorización, urgencia vital o la paciente no autoriza.
3. Busca la cédula. También puedes escribir cualquier otra de la tabla: el campo sugiere las 7.
4. Al encontrar al paciente, el visor propone la nota clínica del caso, salvo que ya hayas escrito la tuya.

Por API:

```bash
curl -X POST localhost:8000/api/simulaciones \
  -H 'Content-Type: application/json' \
  -d '{"escenario": "consentimiento", "medico": "prac-0347"}'
```

`GET /api/catalogo` devuelve `medicos` (con el `endpoint` FHIR de su clínica) y `casos`.

## Resumen

| # | Cédula | Paciente | Clínica (ciudad) | Médico que atiende | Motivo de urgencias | Fuentes |
|---|---|---|---|---|---|---|
| 1 | 1032456789 | Mariana Sofía López Castro | Clínica del Pacífico (Cali) | Dr. Mateo Vargas | Dolor abdominal y fiebre | EPS · IPS · Lab |
| 2 | 79845120 | Jorge Eliecer Pardo Ruiz | Clínica del Pacífico (Cali) | Dr. Mateo Vargas | Dolor torácico | EPS |
| 3 | 1017234567 | Carlos Andrés Gómez Restrepo | Fundación Santa Fe de Bogotá | Dra. Catalina Ríos | Hiperglucemia y malestar general | EPS · IPS · Lab |
| 4 | 52987654 | Luisa Fernanda Rojas Herrera | Centro Médico Chapinero (Bogotá) | Dr. Julián Ortega | Cefalea intensa y cifras tensionales elevadas | EPS · IPS |
| 5 | 1144056789 | Andrés Felipe Martínez Ospina | Hospital Simón Bolívar (Bogotá) | Dr. Sebastián Mejía | Trauma en rodilla derecha por caída de moto | EPS · Lab |
| 6 | 1000345678 | Valentina Ruiz Quintero | Clínica de Marly (Bogotá) | Dra. Natalia Herrera | Cefalea intensa con fotofobia | EPS · IPS · Lab |
| 7 | 19456321 | Héctor Julio Cárdenas Pinzón | Fundación Clínica Cardioinfantil (Bogotá) | Dra. Paula Cifuentes | Disnea progresiva y tos con expectoración | EPS · IPS · Lab |

## Clínicas y médicos

Cada clínica es una IPS de la red (`app/fhir/red.py`) con su endpoint FHIR R4 ficticio. Si el médico elige **enviar la atención a la IPS**, el `Bundle transaction` va al endpoint de *su* clínica.

| ID | Médico | Rol | Clínica | Ciudad | Endpoint FHIR |
|---|---|---|---|---|---|
| `prac-0192` | Dr. Mateo Vargas | Médico de urgencias | Clínica del Pacífico | Cali | `https://fhir.clinicadelpacifico.example/r4` |
| `prac-0347` | Dra. Catalina Ríos | Médica de urgencias | Fundación Santa Fe de Bogotá | Bogotá | `https://fhir.fsfb.example/r4` |
| `prac-0418` | Dr. Julián Ortega | Médico de urgencias | Centro Médico Chapinero | Bogotá | `https://fhir.cmchapinero.example/r4` |
| `prac-0523` | Dra. Paula Cifuentes | Médica de urgencias | Fundación Clínica Cardioinfantil | Bogotá | `https://fhir.cardioinfantil.example/r4` |
| `prac-0611` | Dr. Sebastián Mejía | Médico de urgencias | Hospital Simón Bolívar | Bogotá | `https://fhir.hsimonbolivar.example/r4` |
| `prac-0735` | Dra. Natalia Herrera | Médica de urgencias | Clínica de Marly | Bogotá | `https://fhir.marly.example/r4` |

Si no se elige médico, atiende el Dr. Mateo Vargas, como en el boceto.

Los profesionales que aparecen en las **atenciones anteriores** (Dra. Laura Méndez, Dr. Ricardo Peña, Dr. Hernán Castillo) son de la IPS fuente de datos, Centro Médico Chapinero. Son historia clínica, no médicos de urgencias.

## Detalle por paciente

Las fuentes siguen siendo una sola EPS (EPS Andina), una IPS (Centro Médico Chapinero) y un laboratorio (Laboratorio Bioandes), cada una en su formato nativo. Cada paciente tiene un ID distinto en cada fuente; el MPI los une en `Patient/hc-{cédula}`.

### 1. Mariana Sofía López Castro · CC 1.032.456.789

- **Nacimiento:** 14/03/1992 · F · EPS régimen contributivo
- **IDs locales:** EPS `CC 1032456789` · IPS `P-00417` · Lab `LB-2291`
- **Alergia:** penicilina, **grave** (urticaria generalizada y dificultad para respirar)
- **Atenciones:** control de asma (J45.9, 18 ago 2026); dolor abdominal (R10.4, 6 nov 2026)
- **Fórmula:** salbutamol inhalador 100 mcg
- **Laboratorio** (7 nov 2026), hemograma y proteína C reactiva: leucocitos 13,8 ↑ · hemoglobina 13,1 · plaquetas 310 · PCR 48 ↑
- **Autorización EPS:** ecografía abdominal total (`AUT-88231`)
- **Qué muestra:** el caso del boceto. El médico ve la alergia y no repite el hemograma ni la PCR.

### 2. Jorge Eliecer Pardo Ruiz · CC 79.845.120

- **Nacimiento:** 02/09/1971 · M · EPS régimen subsidiado
- **Solo en la EPS** (`completo = false`). No tiene alergias, atenciones ni exámenes en la red.
- **Qué muestra:** un paciente con información parcial. El nombre sale de la EPS, en mayúsculas y sin tildes, y se capitaliza.

### 3. Carlos Andrés Gómez Restrepo · CC 1.017.234.567

- **Nacimiento:** 22/05/1988 · M · EPS régimen contributivo
- **IDs locales:** EPS `CC 1017234567` · IPS `P-00532` · Lab `LB-2310`
- **Alergia:** sulfonamidas, leve (erupción cutánea pruriginosa)
- **Atención:** control de diabetes en medicina interna (E11.9, 15 sep 2026, Dr. Ricardo Peña)
- **Fórmula:** metformina 850 mg cada 12 horas
- **Laboratorio** (5 nov 2026), perfil glucémico: glucosa en ayunas 182 ↑ · hemoglobina glicosilada 8,4 % ↑ · creatinina 0,9
- **Qué muestra:** un paciente crónico descompensado. La hemoglobina glicosilada es reciente y no se repite.

### 4. Luisa Fernanda Rojas Herrera · CC 52.987.654

- **Nacimiento:** 03/11/1979 · F · EPS régimen contributivo
- **IDs locales:** EPS `CC 52987654` · IPS `P-00588` · sin laboratorio
- **Alergia:** ibuprofeno y otros AINE, **grave** (angioedema facial)
- **Atención:** control de hipertensión (I10, 2 oct 2026, Dra. Laura Méndez)
- **Fórmula:** losartán 50 mg cada 12 horas
- **Autorización EPS:** ecocardiograma transtorácico (`AUT-88412`, 20 oct 2026)
- **Qué muestra:** una alergia grave que cambia la analgesia en urgencias (no se da ibuprofeno para la cefalea).

### 5. Andrés Felipe Martínez Ospina · CC 1.144.056.789

- **Nacimiento:** 15/07/1995 · M · EPS régimen subsidiado
- **IDs locales:** EPS `CC 1144056789` · Lab `LB-2345` · **no está en la IPS**
- **Laboratorio** (28 oct 2026), hemograma: leucocitos 7,2 · hemoglobina 15,1 · plaquetas 250 (todo normal)
- **Autorización EPS:** resonancia magnética de rodilla derecha (`AUT-88507`, 29 oct 2026)
- **Qué muestra:** un paciente joven sin historia en la IPS. Sin la IPS no hay alergias registradas, y el visor lo deja claro.

### 6. Valentina Ruiz Quintero · CC 1.000.345.678

- **Nacimiento:** 30/01/2001 · F · EPS régimen contributivo
- **IDs locales:** EPS `CC 1000345678` · IPS `P-00641` · Lab `LB-2378`
- **Alergia:** látex, leve (dermatitis de contacto)
- **Atención:** cefalea recurrente, migraña (G43.9, 25 jul 2026)
- **Fórmula:** acetaminofén 500 mg si hay dolor
- **Laboratorio** (10 nov 2026), hemograma: leucocitos 6,8 · hemoglobina 11,2 ↓ · plaquetas 280
- **Qué muestra:** una alergia no medicamentosa que importa en urgencias (guantes de nitrilo) y un valor bajo (L).

### 7. Héctor Julio Cárdenas Pinzón · CC 19.456.321

- **Nacimiento:** 12/09/1958 · M · EPS régimen subsidiado
- **IDs locales:** EPS `CC 19456321` · IPS `P-00702` · Lab `LB-2402` y `LB-2403`
- **Alergia:** ácido acetilsalicílico (aspirina), **grave** (broncoespasmo)
- **Atenciones:** control de EPOC en neumología (J44.9, 3 mar 2026); EPOC con exacerbación (J44.1, 30 oct 2026)
- **Fórmula:** tiotropio inhalador 2,5 mcg
- **Laboratorio** (31 oct 2026), **dos órdenes**:
  - Función renal y electrolitos: creatinina 1,4 ↑ · potasio 4,1 · sodio 138
  - Gases arteriales: pH 7,33 ↓ · PaCO2 52 ↑
- **Qué muestra:** el caso más completo (12 recursos FHIR). Cada orden de laboratorio es un item aparte en la línea de tiempo.

## Dónde está cada dato en el código

| Qué | Archivo |
|---|---|
| Médicos (`MEDICOS`, `medico_por_id`) | `backend/app/actores.py` |
| Casos: cédula, médico, motivo y nota sugerida (`CASOS`, `caso_de`) | `backend/app/casos.py` |
| Afiliados y autorizaciones (tabla plana) | `backend/app/sources/eps.py` |
| Pacientes, alergias, atenciones y fórmulas (JSON propio) | `backend/app/sources/ips.py` |
| Resultados de laboratorio (CSV con `;`, columna `examen` = nombre de la orden) | `backend/app/sources/lab.py` |
| Clínicas de la red y su endpoint (`RED_IPS`, `endpoint_de`) | `backend/app/fhir/red.py` |
| Tests de los casos | `backend/tests/test_casos.py` |

## Qué cambió en el backend para soportar los casos

- **Médico por simulación.** `POST /api/simulaciones` acepta `medico` (id; uno desconocido da 422). El médico va en la respuesta (`medico`, con su `endpoint`) y se usa en el Consent (`provision.actor`, `performer` en emergencia), el RDA (`Composition.author`, `Encounter.serviceProvider`), la auditoría y el envío a la IPS, que se hace al endpoint de su clínica.
- **Motivo del RDA por caso.** `Encounter.reasonCode` usa el motivo del caso (antes siempre era "Dolor abdominal y fiebre").
- **Nota sugerida.** Al encontrar al paciente, si la nota es la sugerida, se cambia por la del caso. Si el médico ya escribió la suya, no se toca.
- **Laboratorio por orden.** El CSV tiene la columna `examen`. Cada `Observation` lleva `basedOn` con la orden y su nombre, y la línea de tiempo arma **un item por orden** con ese nombre como título. Los IDs se numeran dentro de cada orden (`obs-LB-2403-1`).
- **pH sin unidad.** Si un analito no tiene unidad, `valueQuantity.unit` se omite, porque FHIR no admite cadenas vacías.
