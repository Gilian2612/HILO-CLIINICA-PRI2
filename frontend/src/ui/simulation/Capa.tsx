// "La capa por dentro": peticiones FHIR, auditoría, recurso FHIR y red de IPS (Np en el boceto).
import { ChevronDown } from 'lucide-react'
import type { Catalogo, RecursoFhir, Simulacion } from '../../api'
import { EtiquetaFuente, horaColombia } from '../comun'

export type Pestana = 'fhir' | 'audit' | 'recurso' | 'red'

const RESULTADO = { ok: 'Permitido', warn: 'Emergencia', deny: 'Denegado' } as const

const textoStatus = (s: number) => (s === 200 ? '200 OK' : s === 201 ? '201 Created' : '403 sin permiso')

export function Capa({
  sim,
  catalogo,
  pestana,
  setPestana,
  inspeccionado,
  abierta,
  setAbierta,
}: {
  sim: Simulacion
  catalogo: Catalogo
  pestana: Pestana
  setPestana: (p: Pestana) => void
  inspeccionado: RecursoFhir | RecursoFhir[] | null
  abierta: boolean
  setAbierta: (v: boolean) => void
}) {
  const { ctx } = sim
  const pestanas: { id: Pestana; label: string; n: number | null }[] = [
    { id: 'fhir', label: 'Peticiones FHIR', n: ctx.log.length },
    { id: 'audit', label: 'Auditoría', n: ctx.auditoria.length },
    { id: 'recurso', label: 'Recurso FHIR', n: null },
    { id: 'red', label: 'Red de IPS', n: catalogo.red.ips.length },
  ]
  const recurso = inspeccionado ?? ctx.envio ?? ctx.rda ?? ctx.consent

  return (
    <section className={`hood ${abierta ? '' : 'is-closed'}`} aria-label="Lo que hace la capa Hilo Clínico">
      <div className="hood-tabs" role="tablist" aria-label="Capa Hilo Clínico">
        <span className="hood-title">La capa por dentro</span>
        {pestanas.map((p) => (
          <button key={p.id} role="tab" id={`tab-${p.id}`} aria-selected={abierta && pestana === p.id}
            aria-controls="hood-panel" className={abierta && pestana === p.id ? 'is-on' : ''}
            onClick={() => setPestana(p.id)}>
            {p.label}
            {p.n !== null && <span className="count">{p.n}</span>}
          </button>
        ))}
        <button className="hood-toggle" aria-expanded={abierta} aria-controls="hood-panel"
          aria-label={abierta ? 'Ocultar la capa por dentro' : 'Mostrar la capa por dentro'}
          onClick={() => setAbierta(!abierta)}>
          <ChevronDown size={18} aria-hidden="true" />
        </button>
      </div>

      <div className="hood-panel" id="hood-panel" role="tabpanel" aria-labelledby={`tab-${pestana}`} tabIndex={0}
        hidden={!abierta}>
        {pestana === 'fhir' &&
          (ctx.log.length === 0 ? (
            <p className="hood-empty">
              Aquí aparecen las consultas a cada fuente. Sin permiso de la paciente, la capa no pide nada.
            </p>
          ) : (
            <table className="log">
              <thead>
                <tr>
                  <th scope="col">Fuente</th>
                  <th scope="col">Petición</th>
                  <th scope="col">Respuesta</th>
                  <th scope="col">Recursos</th>
                </tr>
              </thead>
              <tbody>
                {ctx.log.map((p, i) => (
                  <tr key={i} className={p.status >= 400 ? 'is-denied' : ''}>
                    <td>
                      {p.fuente === 'dest' ? (
                        <span className="source-tag">Sistema de la {catalogo.medico.organizacion}</span>
                      ) : (
                        <EtiquetaFuente fuente={p.fuente} catalogo={catalogo} />
                      )}
                    </td>
                    <td className="mono url">{p.metodo} {p.url}</td>
                    <td className="mono">{textoStatus(p.status)}</td>
                    <td>{p.cantidad}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ))}

        {pestana === 'audit' &&
          (ctx.auditoria.length === 0 ? (
            <p className="hood-empty">
              Cada acceso queda registrado con hora, persona y resultado. Empieza la simulación para ver el registro.
            </p>
          ) : (
            <table className="log">
              <thead>
                <tr>
                  <th scope="col">Hora</th>
                  <th scope="col">Quién</th>
                  <th scope="col">Qué pasó</th>
                  <th scope="col">Resultado</th>
                </tr>
              </thead>
              <tbody>
                {[...ctx.auditoria].reverse().map((a) => (
                  <tr key={a.id + a.accion} className={a.resultado === 'deny' ? 'is-denied' : ''}>
                    <td className="mono">{horaColombia(a.hora)}</td>
                    <td>{a.quien}</td>
                    <td><strong>{a.accion}.</strong> {a.detalle}</td>
                    <td><span className={`pill pill-${a.resultado}`}>{RESULTADO[a.resultado]}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ))}

        {pestana === 'recurso' &&
          (recurso ? (
            <pre className="json mono">{JSON.stringify(recurso, null, 2)}</pre>
          ) : (
            <p className="hood-empty">
              Elige "Ver recurso" en la historia para ver el recurso HL7 FHIR que generó el adaptador.
            </p>
          ))}

        {pestana === 'red' && (
          <>
            <table className="log">
              <thead>
                <tr>
                  <th scope="col">IPS</th>
                  <th scope="col">Ciudad</th>
                  <th scope="col">Endpoint FHIR</th>
                  <th scope="col">Estado</th>
                </tr>
              </thead>
              <tbody>
                {catalogo.red.ips.map((x) => (
                  <tr key={x.nombre}>
                    <td>{x.nombre}</td>
                    <td>{x.ciudad}</td>
                    <td className="mono url">{x.endpoint}</td>
                    <td><span className={`pill pill-${x.estado}`}>{x.rol}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="hood-empty">
              Las IPS marcadas como ejemplo son nombres ilustrativos: no tienen integración real con Hilo Clínico y sus
              endpoints son ficticios.
            </p>
          </>
        )}
      </div>
    </section>
  )
}
