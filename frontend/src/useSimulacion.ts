// Estado de la simulación en el navegador. Todo cambio pasa por la API: aquí solo se
// encolan las peticiones (para que no se crucen) y se marca el ritmo de las animaciones.
import { useCallback, useEffect, useRef, useState } from 'react'
import * as api from './api'
import type { Accion, CambioBorrador, EscenarioId, KindNodo, Proceso, Simulacion } from './api'

/** Duración de la ficha recorriendo un flujo (igual que el boceto). */
export const DURACION_FLUJO_MS = 720

/** Cuánto se queda la ficha en cada tipo de nodo cuando las tareas avanzan solas. */
const PAUSA_POR_KIND: Record<KindNodo, number> = {
  service: 1700,
  send: 1300,
  xor: 650,
  start: 300,
  end: 0,
  user: 0,
}

export interface ControlSimulacion {
  sim: Simulacion | null
  auto: boolean
  setAuto: (v: boolean) => void
  paso: () => void
  atras: () => void
  /** Crea una simulación nueva; conserva el escenario y el médico que no se pasen. */
  reiniciar: (escenario?: EscenarioId, medico?: string) => void
  actuar: (accion: Accion) => void
  editarBorrador: (cambios: CambioBorrador) => void
  revocar: () => void
}

export function useSimulacion(proceso: Proceso | null, alError: (e: unknown) => void): ControlSimulacion {
  const [sim, setSim] = useState<Simulacion | null>(null)
  const [auto, setAuto] = useState(true)
  const simRef = useRef<Simulacion | null>(null)
  const cola = useRef<Promise<unknown>>(Promise.resolve())

  const fijar = useCallback((s: Simulacion) => {
    simRef.current = s
    setSim(s)
  }, [])

  /** Encola una petición que recibe el id actual y devuelve la simulación nueva. */
  const encolar = useCallback(
    (fn: (s: Simulacion | null) => Promise<Simulacion | null>) => {
      cola.current = cola.current
        .then(() => fn(simRef.current))
        .then((s) => s && fijar(s))
        .catch(alError)
    },
    [fijar, alError],
  )

  const reiniciar = useCallback(
    (escenario?: EscenarioId, medico?: string) =>
      encolar(async (s) => {
        const nueva = await api.crearSimulacion(escenario ?? s?.escenario ?? 'consentimiento', {
          medico: medico ?? s?.medico.id,
        })
        if (s) api.borrarSimulacion(s.id).catch(() => {})
        setAuto(true)
        return nueva
      }),
    [encolar],
  )

  useEffect(() => {
    reiniciar('consentimiento')
  }, [reiniciar])

  const paso = useCallback(
    () => encolar(async (s) => (s && s.estado !== 'ended' ? api.paso(s.id) : s)),
    [encolar],
  )
  const atras = useCallback(
    () => encolar(async (s) => (s?.puede_volver ? api.atras(s.id) : s)),
    [encolar],
  )
  const actuar = useCallback(
    (accion: Accion) => encolar(async (s) => (s ? api.actuar(s.id, accion) : s)),
    [encolar],
  )
  const revocar = useCallback(() => encolar(async (s) => (s ? api.revocar(s.id) : s)), [encolar])

  // Lo escrito se refleja al instante y se guarda en el backend sin bloquear el teclado.
  const editarBorrador = useCallback(
    (cambios: CambioBorrador) => {
      const s = simRef.current
      if (!s) return
      fijar({
        ...s,
        ctx: {
          ...s.ctx,
          borrador: { ...s.ctx.borrador, ...cambios },
          error_busqueda: 'documento' in cambios ? null : s.ctx.error_busqueda,
        },
      })
      encolar(async (actual) => {
        if (!actual) return actual
        const r = await api.patchBorrador(actual.id, cambios)
        // Conserva lo que se siguió escribiendo mientras viajaba la petición.
        return { ...r, ctx: { ...r.ctx, borrador: simRef.current?.ctx.borrador ?? r.ctx.borrador } }
      })
    },
    [fijar, encolar],
  )

  // Ritmo: la ficha llega al final del flujo; si "avanzan solas", las tareas de Hilo Clínico
  // terminan tras una pausa según su tipo.
  const nodo = sim?.nodo
  const estado = sim?.estado
  useEffect(() => {
    if (!sim || !proceso) return
    if (estado === 'moving') {
      const t = setTimeout(paso, DURACION_FLUJO_MS)
      return () => clearTimeout(t)
    }
    if (estado === 'running' && auto) {
      const kind = proceso.nodos.find((n) => n.id === nodo)?.kind ?? 'service'
      const t = setTimeout(paso, PAUSA_POR_KIND[kind] ?? 900)
      return () => clearTimeout(t)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [estado, nodo, auto, proceso, paso, sim?.ctx.reloj])

  return { sim, auto, setAuto, paso, atras, reiniciar, actuar, editarBorrador, revocar }
}
