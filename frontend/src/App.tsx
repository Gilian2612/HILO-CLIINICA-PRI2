import { useCallback, useEffect, useState } from 'react'
import { MotionConfig, motion } from 'framer-motion'
import * as api from './api'
import type { Catalogo, Proceso } from './api'
import { useSimulacion } from './useSimulacion'
import { Wordmark } from './ui/Wordmark'
import { VistaSimulacion } from './ui/simulation/VistaSimulacion'

type Vista = 'simulacion' | 'bpmn' | 'impacto'

const VISTAS: { id: Vista; label: string }[] = [
  { id: 'simulacion', label: 'Simulación' },
  { id: 'bpmn', label: 'Proceso BPMN' },
  { id: 'impacto', label: 'Impacto en salud' },
]

export default function App() {
  const [vista, setVista] = useState<Vista>('simulacion')
  const [proceso, setProceso] = useState<Proceso | null>(null)
  const [catalogo, setCatalogo] = useState<Catalogo | null>(null)
  const [error, setError] = useState<string | null>(null)

  const alError = useCallback((e: unknown) => {
    console.error(e)
    setError('Sin conexión con el backend (¿está corriendo en el puerto 8000?)')
  }, [])
  const control = useSimulacion(proceso, alError)
  const { sim } = control

  useEffect(() => {
    Promise.all([api.getProceso(), api.getCatalogo()])
      .then(([p, c]) => {
        setProceso(p)
        setCatalogo(c)
      })
      .catch(alError)
  }, [alError])

  // Teclas ← → como en el boceto, salvo al escribir en un campo.
  useEffect(() => {
    const alPulsar = (e: KeyboardEvent) => {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return
      if (e.altKey || e.metaKey || e.ctrlKey) return
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) return
      if (e.key === 'ArrowLeft') control.atras()
      else control.paso()
    }
    window.addEventListener('keydown', alPulsar)
    return () => window.removeEventListener('keydown', alPulsar)
  }, [control])

  const listo = sim && proceso && catalogo

  return (
    <MotionConfig reducedMotion="user">
      <a className="skip" href="#main">
        Saltar al contenido
      </a>
      <header className="top">
        <div className="brand">
          <Wordmark />
          <span className="brand-tag">Prototipo del MVP, con datos ficticios</span>
        </div>
        <nav className="views" aria-label="Vistas del prototipo">
          {VISTAS.map((v) => (
            <button key={v.id} className={vista === v.id ? 'is-on' : ''}
              aria-current={vista === v.id ? 'page' : undefined} onClick={() => setVista(v.id)}>
              {v.label}
              {vista === v.id && <motion.span layoutId="view-underline" className="views-line" />}
            </button>
          ))}
        </nav>
        <fieldset className="scenario">
          <legend>Escenario</legend>
          {proceso?.escenarios.map((e) => (
            <label key={e.id} className={sim?.escenario === e.id ? 'is-on' : ''} title={e.blurb}>
              <input type="radio" name="escenario" value={e.id} checked={sim?.escenario === e.id}
                onChange={() => control.reiniciar(e.id)} />
              {e.label}
            </label>
          ))}
        </fieldset>
      </header>

      {error && !listo && (
        <main id="main" className="view" style={{ padding: 32 }}>
          <p style={{ color: 'var(--coral-deep)', fontWeight: 700 }}>{error}</p>
        </main>
      )}

      {listo && vista === 'simulacion' && (
        <VistaSimulacion sim={sim} proceso={proceso} catalogo={catalogo} control={control}
          irAImpacto={() => setVista('impacto')} />
      )}

      {listo && vista !== 'simulacion' && (
        // Provisional: las vistas BPMN (paso 4) e Impacto (paso 6) aún no están.
        <main id="main" className="view" style={{ padding: 32 }}>
          <h1>{VISTAS.find((v) => v.id === vista)?.label}</h1>
          <p style={{ color: 'var(--ink-soft)' }}>Vista en construcción.</p>
        </main>
      )}
    </MotionConfig>
  )
}
