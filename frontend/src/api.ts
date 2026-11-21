// Cliente de la API de Hilo Clínico.
// El frontend no decide nada: solo pide el estado al backend y lo pinta.

// ---------- Tipos: catálogos ----------

export type FuenteId = 'eps' | 'ips' | 'lab'
export type EscenarioId = 'consentimiento' | 'emergencia' | 'rechazo'
export type KindNodo = 'start' | 'end' | 'user' | 'service' | 'send' | 'xor'
export type Punto = [number, number]

export interface Carril { id: string; nombre: string }
export interface Pool { id: string; nombre: string }
export interface Nodo {
  id: string
  kind: KindNodo
  carril: string
  nombre: string
  cx: number
  cy: number
  ayuda: string
  label_at: Punto | null
}
export interface Flujo {
  id: string
  desde: string
  hacia: string
  puntos: Punto[]
  nombre: string
  label_at: Punto | null
}
export interface Escenario { id: EscenarioId; label: string; blurb: string }

export interface Proceso {
  carriles: Carril[]
  pools: Pool[]
  nodos: Nodo[]
  flujos: Flujo[]
  mensajes: Flujo[]
  escenarios: Escenario[]
}

export interface Fuente {
  id: FuenteId
  tipo: string
  nombre: string
  ciudad: string
  formato: string
  color: string
}
export interface Categoria { id: string; etiqueta: string; tipos: string[] }
export interface Medico {
  id: string
  nombre: string
  rol: string
  organizacion: string
  ciudad: string
  display: string
}
export interface IpsRed {
  nombre: string
  ciudad: string
  endpoint: string
  rol: string
  estado: string
}
export interface Catalogo {
  fuentes: Fuente[]
  categorias: Categoria[]
  medico: Medico
  red: { endpoint: string; ips: IpsRed[] }
}

// ---------- Tipos: simulación ----------

/** Un recurso FHIR R4 en JSON estándar (lo valida el backend). */
export type RecursoFhir = { resourceType: string; id?: string; [k: string]: unknown }

export type Estado = 'waiting' | 'running' | 'moving' | 'ended'
export type Destino = 'hilo' | 'ips'
export type Decision = 'granted' | 'denied'

export interface Borrador {
  documento: string
  emergencia: boolean
  categorias: string[]
  nota: string
  destino: Destino
}

export interface PacienteMaestro {
  id: string
  documento: string
  documento_label: string
  nombre: string
  nombres: string
  fecha_nacimiento: string
  sexo: 'female' | 'male'
  completo: boolean
}
export interface Identidad {
  fuente: FuenteId
  id_local: string
  como: string
  nacimiento: string | null
}

export interface Peticion {
  /** 'dest' es el sistema de la IPS que atiende (envío de la atención). */
  fuente: FuenteId | 'dest'
  tipo: string
  metodo: string
  url: string
  status: number
  cantidad: number
}

export interface Analito {
  nombre: string
  valor: number
  unidad: string
  bandera: 'H' | 'L' | 'N'
}
export interface ItemLinea {
  id: string
  fecha: string
  tipo: 'laboratorio' | 'consulta' | 'formula' | 'autorizacion'
  fuente: FuenteId
  titulo: string
  subtitulo: string
  detalle: [string, string][]
  recursos: RecursoFhir[]
  fecha_label: string
  hace: string
  reciente: boolean
  analitos: Analito[]
}
export interface Alergia {
  sustancia: string
  reaccion: string
  critica: boolean
  desde: string
  fuente: FuenteId
  recurso: RecursoFhir
}
export interface LineaTiempo {
  items: ItemLinea[]
  alergias: Alergia[]
  cobertura: RecursoFhir | null
}

export interface EventoAuditoria {
  id: string
  hora: string
  quien: string
  accion: string
  detalle: string
  resultado: 'ok' | 'warn' | 'deny'
}

export interface Contexto {
  borrador: Borrador
  error_busqueda: 'corto' | 'no-existe' | null
  emergencia: boolean
  mpi: { paciente: PacienteMaestro; identidades: Identidad[] } | null
  solicitud: 'pending' | Decision | null
  decision: Decision | null
  consent: RecursoFhir | null
  revocado: boolean
  log: Peticion[]
  recursos: RecursoFhir[]
  linea: LineaTiempo | null
  nota: string
  destino: Destino
  rda: RecursoFhir | null
  envio: RecursoFhir | null
  auditoria: EventoAuditoria[]
  reloj: number
}

export interface Simulacion {
  id: string
  escenario: EscenarioId
  inicio: string
  ahora: string
  nodo: string
  estado: Estado
  visitados: string[]
  flujos: string[]
  /** Lo recorrido más el camino previsto (sin inicio ni uniones), para la barra de pasos. */
  ruta: string[]
  en_movimiento: { flujo: string; desde: string; hacia: string } | null
  puede_volver: boolean
  ctx: Contexto
}

/** Lo que el médico o la paciente envían al actuar. Solo se mandan los campos presentes. */
export interface Accion {
  documento?: string
  emergencia?: boolean
  decision?: Decision
  categorias?: string[]
  nota?: string
  destino?: Destino
}
export type CambioBorrador = Partial<Borrador>

// ---------- Llamadas ----------

export class ErrorApi extends Error {
  status: number
  constructor(status: number, mensaje: string) {
    super(mensaje)
    this.status = status
  }
}

async function pedir<T>(metodo: string, ruta: string, cuerpo?: unknown): Promise<T> {
  const r = await fetch(`/api${ruta}`, {
    method: metodo,
    headers: cuerpo === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  })
  if (!r.ok) throw new ErrorApi(r.status, `${metodo} ${ruta} → ${r.status}`)
  return (r.status === 204 ? undefined : await r.json()) as T
}

export const getProceso = () => pedir<Proceso>('GET', '/proceso')
export const getCatalogo = () => pedir<Catalogo>('GET', '/catalogo')

export const crearSimulacion = (escenario: EscenarioId, inicio?: string) =>
  pedir<Simulacion>('POST', '/simulaciones', inicio ? { escenario, inicio } : { escenario })
export const getSimulacion = (id: string) => pedir<Simulacion>('GET', `/simulaciones/${id}`)
export const borrarSimulacion = (id: string) => pedir<void>('DELETE', `/simulaciones/${id}`)

export const paso = (id: string) => pedir<Simulacion>('POST', `/simulaciones/${id}/paso`)
export const actuar = (id: string, accion: Accion) =>
  pedir<Simulacion>('POST', `/simulaciones/${id}/actuar`, accion)
export const patchBorrador = (id: string, cambios: CambioBorrador) =>
  pedir<Simulacion>('PATCH', `/simulaciones/${id}/borrador`, cambios)
export const revocar = (id: string) => pedir<Simulacion>('POST', `/simulaciones/${id}/revocar`)
export const atras = (id: string) => pedir<Simulacion>('POST', `/simulaciones/${id}/atras`)
