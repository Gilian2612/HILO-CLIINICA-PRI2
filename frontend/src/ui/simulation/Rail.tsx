// Barra lateral "Proceso TO-BE": pasos de la ruta y controles (iy + ny en el boceto).
import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Check, RotateCcw, SkipForward } from 'lucide-react'
import type { Proceso, Simulacion } from '../../api'
import type { ControlSimulacion } from '../../useSimulacion'

type Actor = 'medico' | 'hilo' | 'paciente'

const ACTOR_DE_CARRIL: Record<string, Actor> = {
  lane_medico: 'medico',
  lane_hilo: 'hilo',
  lane_paciente: 'paciente',
}
const NOMBRE_ACTOR: Record<Actor, string> = { medico: 'Médico', hilo: 'Hilo Clínico', paciente: 'Paciente' }

export const TURNO: Record<string, string> = {
  t_buscar: 'Turno del médico: buscar al paciente en el visor.',
  t_resp: 'Turno de la paciente: responder la solicitud en su app.',
  t_atender: 'Turno del médico: revisar la historia y registrar la atención.',
}

/** Respuesta que se muestra junto a una compuerta ya resuelta. */
function respuesta(nodo: string, sim: Simulacion) {
  if (nodo === 'g_urg') return sim.ctx.emergencia ? 'Sí' : 'No'
  if (nodo === 'g_aut') return sim.ctx.decision === 'granted' ? 'Sí' : 'No'
  if (nodo === 'g_dest') return sim.ctx.destino === 'ips' ? 'En la IPS' : 'En Hilo Clínico'
  return ''
}

export function Rail({ sim, proceso, control }: { sim: Simulacion; proceso: Proceso; control: ControlSimulacion }) {
  const lista = useRef<HTMLOListElement>(null)
  const actual = sim.ruta.indexOf(sim.nodo)
  const nodo = (id: string) => proceso.nodos.find((n) => n.id === id)!

  useEffect(() => {
    lista.current?.querySelector('.step-current')?.scrollIntoView({ block: 'nearest' })
  }, [sim.nodo])

  return (
    <aside className="rail" aria-label="Pasos del proceso">
      <h2 className="rail-title">Proceso TO-BE</h2>
      <p className="rail-sub">Urgencias en una IPS que no conoce a la paciente.</p>
      <ol className="steps" ref={lista}>
        {sim.ruta.map((id, i) => {
          const n = nodo(id)
          const actor = ACTOR_DE_CARRIL[n.carril]
          const estado =
            i < actual || (sim.estado === 'ended' && i <= actual) ? 'done' : i === actual ? 'current' : 'todo'
          const esCompuerta = n.kind === 'xor'
          return (
            <li
              key={id}
              className={`step step-${estado} ${esCompuerta ? 'step-gw' : ''}`}
              aria-current={estado === 'current' ? 'step' : undefined}
            >
              <span className="step-knot" aria-hidden="true">
                {estado === 'done' && <Check size={12} strokeWidth={3} />}
              </span>
              <div>
                <span className="step-name">
                  {n.nombre}
                  {esCompuerta && estado === 'done' ? ` ${respuesta(id, sim)}` : ''}
                </span>
                {estado === 'current' && n.ayuda && (
                  <motion.p className="step-help" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
                    {n.ayuda}
                  </motion.p>
                )}
              </div>
              {!esCompuerta && <span className={`step-actor actor-${actor}`}>{NOMBRE_ACTOR[actor]}</span>}
            </li>
          )
        })}
      </ol>
      <Controles sim={sim} proceso={proceso} control={control} />
    </aside>
  )
}

export function FlechaAtras() {
  return (
    <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="m12 19-7-7 7-7" />
      <path d="M19 12H5" />
    </svg>
  )
}

function Controles({ sim, proceso, control }: { sim: Simulacion; proceso: Proceso; control: ControlSimulacion }) {
  const terminado = sim.estado === 'ended'
  const n = proceso.nodos.find((x) => x.id === sim.nodo)!
  const pista = terminado
    ? 'El proceso terminó.'
    : sim.estado === 'waiting'
      ? TURNO[sim.nodo]
      : `${NOMBRE_ACTOR[ACTOR_DE_CARRIL[n.carril]]} está trabajando: ${(n.nombre || 'unir caminos').toLowerCase()}.`

  return (
    <div className="controls">
      <p className="controls-hint" aria-live="polite">
        {pista}
      </p>
      <div className="controls-row">
        <button className="btn btn-ghost btn-icon" onClick={control.atras} disabled={!sim.puede_volver}
          aria-label="Paso anterior" title="Paso anterior">
          <FlechaAtras />
        </button>
        {terminado ? (
          <button className="btn btn-primary" onClick={() => control.reiniciar()}>
            <RotateCcw size={18} aria-hidden="true" />
            Repetir la simulación
          </button>
        ) : (
          <button className="btn btn-primary" onClick={control.paso}>
            <SkipForward size={18} aria-hidden="true" />
            Siguiente paso
          </button>
        )}
        {!terminado && (
          <button className="btn btn-ghost btn-icon" onClick={() => control.reiniciar()}
            aria-label="Reiniciar la simulación" title="Reiniciar">
            <RotateCcw size={18} aria-hidden="true" />
          </button>
        )}
      </div>
      <label className="switch">
        <input type="checkbox" role="switch" checked={control.auto} onChange={(e) => control.setAuto(e.target.checked)} />
        <span className="switch-track" aria-hidden="true" />
        <span>Las tareas de Hilo Clínico avanzan solas</span>
      </label>
    </div>
  )
}
