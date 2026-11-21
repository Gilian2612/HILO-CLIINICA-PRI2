// Vista "Simulación": barra de pasos, visor del médico + capa por dentro, y app de la paciente.
import { useEffect, useState } from 'react'
import { Smartphone, Stethoscope } from 'lucide-react'
import type { Catalogo, Proceso, RecursoFhir, Simulacion } from '../../api'
import type { ControlSimulacion } from '../../useSimulacion'
import phoneBlob from '../../assets/phone-blob.svg'
import { Nudo } from '../comun'
import { Capa, type Pestana } from './Capa'
import { Rail } from './Rail'
import { Telefono } from './Telefono'
import { Visor } from './Visor'

export function VistaSimulacion({
  sim,
  proceso,
  catalogo,
  control,
  irAImpacto,
}: {
  sim: Simulacion
  proceso: Proceso
  catalogo: Catalogo
  control: ControlSimulacion
  irAImpacto: () => void
}) {
  const [pestana, setPestana] = useState<Pestana>('audit')
  const [inspeccionado, setInspeccionado] = useState<RecursoFhir | RecursoFhir[] | null>(null)
  const [pantalla, setPantalla] = useState<'medico' | 'paciente'>('medico')
  const [capaAbierta, setCapaAbierta] = useState(true)

  // Igual que el boceto: la capa y la pantalla siguen al proceso.
  useEffect(() => {
    if (sim.nodo === 't_fhir') setPestana('fhir')
    if (sim.nodo === 't_cerrar' || sim.nodo === 't_envio') {
      setInspeccionado(null)
      setPestana('recurso')
    }
    if (sim.nodo === 't_resp') setPantalla('paciente')
    if (sim.nodo === 't_atender' || sim.nodo === 't_buscar') setPantalla('medico')
    if (sim.nodo === 't_atender' && window.innerHeight < 820) setCapaAbierta(false)
    if (sim.nodo === 't_cerrar' || sim.nodo === 't_fhir' || sim.nodo === 't_envio') setCapaAbierta(true)
  }, [sim.nodo])

  useEffect(() => {
    if (sim.visitados.length <= 2) setInspeccionado(null)
  }, [sim.visitados.length])

  const inspeccionar = (r: RecursoFhir | RecursoFhir[]) => {
    setInspeccionado(r)
    setPestana('recurso')
    setCapaAbierta(true)
  }

  return (
    <main className="view view-sim" id="main">
      <Rail sim={sim} proceso={proceso} control={control} />
      <div className="pane-switch" role="tablist" aria-label="Pantalla">
        <button role="tab" aria-selected={pantalla === 'medico'} className={pantalla === 'medico' ? 'is-on' : ''}
          onClick={() => setPantalla('medico')}>
          <Stethoscope size={16} aria-hidden="true" />
          Médico
        </button>
        <button role="tab" aria-selected={pantalla === 'paciente'} className={pantalla === 'paciente' ? 'is-on' : ''}
          onClick={() => setPantalla('paciente')}>
          <Smartphone size={16} aria-hidden="true" />
          Paciente
        </button>
      </div>
      <div className={`stage pane-${pantalla}`}>
        <div className="stage-medico">
          <Visor sim={sim} catalogo={catalogo} control={control} alInspeccionar={inspeccionar} irAImpacto={irAImpacto} />
          <Capa sim={sim} catalogo={catalogo} pestana={pestana}
            setPestana={(p) => { setPestana(p); setCapaAbierta(true) }}
            inspeccionado={inspeccionado} abierta={capaAbierta} setAbierta={setCapaAbierta} />
        </div>
        <div className="stage-paciente">
          <img src={phoneBlob} alt="" className="phone-blob" />
          <Telefono sim={sim} catalogo={catalogo} control={control} />
          <ul className="sources-key" aria-label="Fuentes de datos">
            {catalogo.fuentes.map((f) => (
              <li key={f.id}>
                <Nudo fuente={f.id} size={12} />
                {f.tipo}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </main>
  )
}
