// Visor clínico del médico (Vp y sus pantallas en el boceto).
import { Fragment, useEffect, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import {
  BadgeCheck, Ban, Braces, Check, ChevronDown, CircleCheck, FileText, FlaskConical, Lock, Pill,
  Search, Send, ShieldCheck, Siren, Stethoscope, TriangleAlert,
} from 'lucide-react'
import type { Catalogo, ItemLinea, RecursoFhir, Simulacion } from '../../api'
import type { ControlSimulacion } from '../../useSimulacion'
import avatarMedico from '../../assets/avatar-medico.svg'
import { Aviso, EtiquetaFuente, Nudo, aparecer, edad, fechaCorta, fuenteDe } from '../comun'

type Etapa =
  | 'search' | 'matching' | 'waiting' | 'opening' | 'denied' | 'fetching'
  | 'history' | 'revoked' | 'closing' | 'closed'

/** Qué pantalla del visor corresponde al nodo actual. */
function etapa(sim: Simulacion): Etapa {
  const { ctx } = sim
  if (!ctx.mpi) return 'search'
  switch (sim.nodo) {
    case 't_buscar': case 't_mpi': case 'g_urg': return 'matching'
    case 't_solic': case 't_resp': return 'waiting'
    case 'g_aut': return ctx.decision === 'granted' ? 'opening' : 'denied'
    case 'end_no': return 'denied'
    case 't_emerg': case 'g_join': return 'opening'
    case 't_fhir': return 'fetching'
    case 't_atender': return ctx.revocado ? 'revoked' : 'history'
    case 'g_dest': case 't_guardar': case 't_envio': case 'g_dj': case 't_cerrar': return 'closing'
    case 'end_ok': return 'closed'
    default: return 'search'
  }
}

export interface PropsVisor {
  sim: Simulacion
  catalogo: Catalogo
  control: ControlSimulacion
  alInspeccionar: (r: RecursoFhir | RecursoFhir[]) => void
  irAImpacto: () => void
}

export function Visor({ sim, catalogo, control, alInspeccionar, irAImpacto }: PropsVisor) {
  const e = etapa(sim)
  const { ctx } = sim
  const { medico } = sim
  const paciente = ctx.mpi?.paciente
  const primerNombre = paciente?.nombres.split(' ')[0] ?? ''
  const turno = sim.estado === 'waiting' && (sim.nodo === 't_buscar' || sim.nodo === 't_atender')
  const cobertura = ctx.linea?.cobertura as { type?: { text?: string } } | null | undefined

  return (
    <section className={`visor ${turno ? 'has-turn' : ''}`} aria-label="Visor clínico del médico">
      <header className="visor-bar">
        <div>
          <p className="visor-org">{medico.organizacion}, {medico.ciudad}</p>
          <h2 className="visor-title">Visor clínico de urgencias</h2>
        </div>
        <div className="who">
          <span className="who-text">
            <strong>{medico.nombre}</strong>
            <span>{medico.rol}</span>
          </span>
          <span className="avatar avatar-medico" aria-hidden="true">
            <img src={avatarMedico} alt="" />
          </span>
        </div>
      </header>

      {paciente && e !== 'search' && (
        <div className="patient">
          <div>
            <h3 className="patient-name">{paciente.nombre}</h3>
            <p className="patient-meta">
              {edad(paciente.fecha_nacimiento, sim.ahora)} años, {paciente.documento_label}
              {cobertura?.type?.text && !ctx.revocado
                ? `, ${cobertura.type.text.toLowerCase()} en ${fuenteDe(catalogo, 'eps').nombre}`
                : ''}
            </p>
          </div>
          <EstadoAcceso sim={sim} etapa={e} />
        </div>
      )}

      <div className="visor-body">
        <AnimatePresence mode="wait">
          {e === 'search' && <Busqueda catalogo={catalogo} key="search" sim={sim} control={control} />}
          {e === 'matching' && <Union key="matching" sim={sim} catalogo={catalogo} />}
          {e === 'waiting' && (
            <Aviso key="waiting" icono={<Lock size={22} />} tono="lock"
              titulo={`Esperando la autorización de ${primerNombre}`}
              texto="La solicitud ya está en su app. Hasta que responda, Hilo Clínico no consulta ninguna fuente." />
          )}
          {e === 'opening' && (
            <Aviso key="opening"
              icono={ctx.emergencia ? <Siren size={22} /> : <ShieldCheck size={22} />}
              titulo={ctx.emergencia ? 'Acceso de emergencia abierto' : 'Acceso autorizado'}
              texto={ctx.emergencia
                ? 'Queda registrado a tu nombre y la paciente recibirá el aviso.'
                : 'Hilo Clínico va a consultar solo lo que la paciente permitió.'} />
          )}
          {e === 'fetching' && <Consulta key="fetching" sim={sim} catalogo={catalogo} />}
          {e === 'history' && (
            <Historia key="history" sim={sim} catalogo={catalogo} control={control} alInspeccionar={alInspeccionar} />
          )}
          {e === 'revoked' && (
            <Aviso key="revoked" icono={<Lock size={22} />} tono="lock"
              titulo={`${primerNombre} revocó el acceso`}
              texto="La historia dejó de estar visible. Puedes registrar la atención con lo que ya revisaste.">
              <button className="btn btn-primary" onClick={() => registrar(sim, control)}>Registrar atención</button>
            </Aviso>
          )}
          {e === 'closing' && (
            <Aviso key="closing" icono={<Send size={22} />} ocupado titulo="Guardando la atención"
              texto={ctx.destino === 'ips'
                ? `Se envía la atención por API FHIR al sistema de la ${medico.organizacion}, se registra el acceso en la auditoría y se envía el RDA al IHCE.`
                : 'Se registra el acceso en la auditoría y se envía el Resumen Digital de Atención (RDA) al IHCE.'} />
          )}
          {e === 'closed' && (
            <Aviso key="closed" icono={<CircleCheck size={22} />} tono="ok" titulo="Atención registrada"
              texto={ctx.destino === 'ips'
                ? `La atención quedó en el sistema de la ${medico.organizacion} (POST FHIR simulado, 201 Created). Hilo Clínico guarda solo la referencia y la auditoría. El RDA llegó al IHCE y la paciente ya puede ver quién consultó su historia.`
                : 'El RDA quedó recibido por el IHCE (envío simulado) y la paciente ya puede ver quién consultó su historia.'}>
              <button className="btn btn-primary" onClick={irAImpacto}>Ver el impacto de esta atención</button>
              <button className="btn btn-ghost" onClick={() => control.reiniciar()}>Repetir la simulación</button>
            </Aviso>
          )}
          {e === 'denied' && (
            <Aviso key="denied" icono={<Ban size={22} />} tono="lock"
              titulo={`${primerNombre} no autorizó el acceso`}
              texto="No se consultó ninguna fuente. Atiende con lo que ella te cuente; el rechazo quedó en la auditoría.">
              <button className="btn btn-ghost" onClick={() => control.reiniciar()}>Repetir la simulación</button>
            </Aviso>
          )}
        </AnimatePresence>
      </div>
    </section>
  )
}

const registrar = (sim: Simulacion, control: ControlSimulacion) =>
  control.actuar({ nota: sim.ctx.borrador.nota, destino: sim.ctx.borrador.destino })

function EstadoAcceso({ sim, etapa: e }: { sim: Simulacion; etapa: Etapa }) {
  const { ctx } = sim
  if (ctx.consent?.status === 'active') {
    return ctx.emergencia ? (
      <span className="badge badge-warn"><Siren size={14} aria-hidden="true" />Acceso de emergencia, auditado</span>
    ) : (
      <span className="badge badge-ok"><ShieldCheck size={14} aria-hidden="true" />Autorizado por la paciente, 24 h</span>
    )
  }
  if (ctx.revocado) return <span className="badge badge-lock"><Lock size={14} aria-hidden="true" />Acceso revocado</span>
  if (e === 'denied') return <span className="badge badge-lock"><Ban size={14} aria-hidden="true" />Sin autorización</span>
  return <span className="badge badge-lock"><Lock size={14} aria-hidden="true" />Historia bloqueada</span>
}

function Busqueda({ sim, catalogo, control }: { sim: Simulacion; catalogo: Catalogo; control: ControlSimulacion }) {
  const caso = catalogo.casos.find((c) => c.medico === sim.medico.id) ?? catalogo.casos[0]
  const { borrador, error_busqueda } = sim.ctx
  const error =
    error_busqueda === 'corto'
      ? 'Escribe el número completo del documento.'
      : error_busqueda === 'no-existe'
        ? 'Ningún actor conectado tiene ese documento. Revisa el número.'
        : null
  return (
    <motion.form className="search" {...aparecer} noValidate
      onSubmit={(ev) => {
        ev.preventDefault()
        control.actuar({ documento: borrador.documento, emergencia: borrador.emergencia })
      }}>
      <h3>¿A quién vas a atender?</h3>
      <p className="search-lead">
        Busca por documento. Hilo Clínico reconoce a la persona en su EPS, sus IPS y sus laboratorios.
      </p>
      <div className="field-row">
        <label className="field field-sm">
          <span>Tipo</span>
          <select defaultValue="CC" aria-label="Tipo de documento">
            <option value="CC">Cédula</option>
            <option value="TI">Tarjeta de identidad</option>
            <option value="CE">Cédula de extranjería</option>
          </select>
        </label>
        <label className="field">
          <span>Número de documento</span>
          <input inputMode="numeric" autoComplete="off" list="casos-ejemplo" value={borrador.documento} aria-invalid={!!error}
            aria-describedby="doc-help" onChange={(ev) => control.editarBorrador({ documento: ev.target.value })} />
        </label>
      </div>
      <datalist id="casos-ejemplo">
        {catalogo.casos.map((c) => (
          <option key={c.documento} value={c.documento}>{c.nombre}</option>
        ))}
      </datalist>
      <p id="doc-help" className={error ? 'field-error' : 'field-help'} role={error ? 'alert' : undefined}>
        {error || `El caso de ejemplo en esta clínica es ${caso.nombre}, con cédula ${caso.documento}.`}
      </p>
      <label className="check">
        <input type="checkbox" checked={borrador.emergencia}
          onChange={(ev) => control.editarBorrador({ emergencia: ev.target.checked })} />
        <span>
          <strong>Es una urgencia vital</strong> y la paciente no puede autorizar. El acceso se abre de inmediato y
          queda auditado a mi nombre.
        </span>
      </label>
      <button type="submit" className="btn btn-primary btn-turn">
        <Search size={18} aria-hidden="true" />
        Buscar paciente
      </button>
    </motion.form>
  )
}

/** "Tres registros distintos, una sola persona": los hilos de colores se unen en el MPI. */
function Union({ sim, catalogo }: { sim: Simulacion; catalogo: Catalogo }) {
  const quieto = useReducedMotion()
  const { paciente, identidades } = sim.ctx.mpi!
  const alturas = [36, 104, 172]
  return (
    <motion.div className="match" {...aparecer}>
      <p className="match-lead">Tres registros distintos, una sola persona.</p>
      <div className="match-grid">
        <ul className="match-sources">
          {identidades.map((r) => (
            <li key={r.fuente}>
              <Nudo fuente={r.fuente} size={14} />
              <div>
                <strong>{fuenteDe(catalogo, r.fuente).nombre}</strong>
                <span className="mono">{r.id_local}</span>
                <span>{r.como}</span>
              </div>
            </li>
          ))}
        </ul>
        <svg className="match-thread" viewBox="0 0 160 208" preserveAspectRatio="none" aria-hidden="true">
          {identidades.map((r, i) => (
            <motion.path key={r.fuente} d={`M0 ${alturas[i]} C70 ${alturas[i]}, 80 104, 160 104`}
              stroke={fuenteDe(catalogo, r.fuente).color} strokeWidth="3" fill="none" strokeLinecap="round"
              initial={{ pathLength: quieto ? 1 : 0 }} animate={{ pathLength: 1 }}
              transition={{ duration: 0.9, delay: 0.15 + i * 0.18, ease: 'easeInOut' }} />
          ))}
        </svg>
        <motion.div className="match-one" initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: quieto ? 0 : 1.1, duration: 0.3 }}>
          <span className="match-one-label">Índice maestro</span>
          <strong>{paciente.nombre}</strong>
          <span className="mono">{paciente.id}</span>
        </motion.div>
      </div>
    </motion.div>
  )
}

/** Consulta a las fuentes: el contador avanza petición por petición. */
function Consulta({ sim, catalogo }: { sim: Simulacion; catalogo: Catalogo }) {
  const quieto = useReducedMotion()
  const log = sim.ctx.log.filter((p) => p.fuente !== 'dest')
  const [vistas, setVistas] = useState(quieto ? log.length : 0)
  useEffect(() => {
    if (quieto) return setVistas(log.length)
    const t = setInterval(() => setVistas((v) => Math.min(log.length, v + 1)), 190)
    return () => clearInterval(t)
  }, [log.length, quieto])

  return (
    <motion.div className="fetch" {...aparecer}>
      <p className="match-lead">Trayendo y uniendo los datos que la paciente permitió.</p>
      <ul className="fetch-sources">
        {(['eps', 'ips', 'lab'] as const).map((id) => {
          const f = fuenteDe(catalogo, id)
          const deEsta = log.map((p, i) => ({ ...p, i })).filter((p) => p.fuente === id)
          const listas = deEsta.filter((p) => p.i < vistas)
          const total = listas.reduce((s, p) => s + p.cantidad, 0)
          const hecho = listas.length === deEsta.length
          return (
            <li key={id} className={hecho ? 'is-done' : ''}>
              <Nudo fuente={id} size={14} />
              <div>
                <strong>{f.nombre}</strong>
                <span>{f.tipo}, formato {f.formato.toLowerCase()}</span>
              </div>
              <span className="fetch-count" aria-live="polite">
                {hecho ? (total ? `${total} recursos FHIR` : 'Sin permiso') : 'Consultando'}
              </span>
            </li>
          )
        })}
      </ul>
    </motion.div>
  )
}

const ICONO_ITEM = { laboratorio: FlaskConical, consulta: Stethoscope, formula: Pill, autorizacion: FileText }

/** Rango de referencia "4,5 a 11" tomado de la Observation del analito. */
function rango(item: ItemLinea, nombre: string) {
  const obs = item.recursos.find((r) => (r.code as { text?: string })?.text === nombre) as
    | { referenceRange?: { low?: { value: number }; high?: { value: number } }[] }
    | undefined
  const rr = obs?.referenceRange?.[0]
  return rr ? `${rr.low?.value} a ${rr.high?.value}`.replace(/\./g, ',') : ''
}

function Historia({ sim, catalogo, control, alInspeccionar }: Omit<PropsVisor, 'irAImpacto'>) {
  const quieto = useReducedMotion()
  const { linea, consent, borrador } = sim.ctx
  const items = linea?.items ?? []
  const [abierto, setAbierto] = useState<string | null>(items[0]?.id ?? null)
  const labReciente = items.find((i) => i.tipo === 'laboratorio' && i.reciente)
  // Categorías que la paciente no compartió: las que no aparecen en provision.class del Consent.
  const tiposPermitidos = new Set(
    ((consent?.provision as { class?: { code: string }[] })?.class ?? []).map((c) => c.code),
  )
  const noCompartidas = catalogo.categorias.filter((c) => !c.tipos.some((t) => tiposPermitidos.has(t)))

  return (
    <motion.div className="history" {...aparecer}>
      <div className="history-main">
        {linea?.alergias.map((a) => (
          <motion.div key={a.sustancia} className="alert" role="alert" initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: quieto ? 0 : 0.15, type: 'spring', stiffness: 300, damping: 24 }}>
            <TriangleAlert size={22} aria-hidden="true" />
            <div>
              <strong>Alergia grave: {a.sustancia.toLowerCase()}</strong>
              <span>{a.reaccion}. Registrada el {a.desde} en {fuenteDe(catalogo, a.fuente).nombre}.</span>
            </div>
            <button className="link" onClick={() => alInspeccionar(a.recurso)}>Ver recurso</button>
          </motion.div>
        ))}
        {labReciente && (
          <div className="no-repeat">
            <BadgeCheck size={18} aria-hidden="true" />
            <span>
              <strong>No hace falta repetir:</strong> {labReciente.titulo.toLowerCase()} de {labReciente.hace}.
            </span>
          </div>
        )}
        {noCompartidas.length > 0 && (
          <p className="scope-note">
            <Lock size={14} aria-hidden="true" />
            La paciente no compartió: {noCompartidas.map((c) => c.etiqueta.toLowerCase()).join('; ')}.
          </p>
        )}
        <ol className="thread">
          <motion.span className="thread-line" aria-hidden="true" initial={{ scaleY: quieto ? 1 : 0 }}
            animate={{ scaleY: 1 }} transition={{ duration: 0.9, ease: 'easeOut' }} />
          {items.map((m, i) => {
            const Icono = ICONO_ITEM[m.tipo]
            const esAbierto = abierto === m.id
            const fuente = fuenteDe(catalogo, m.fuente)
            return (
              <motion.li key={m.id} className={`event ${esAbierto ? 'is-open' : ''}`}
                initial={{ opacity: 0, x: quieto ? 0 : -8 }} animate={{ opacity: 1, x: 0 }}
                transition={{ delay: quieto ? 0 : 0.25 + i * 0.12, duration: 0.25 }}>
                <span className="event-knot"><Nudo fuente={m.fuente} size={16} title={fuente.tipo} /></span>
                <button className="event-head" aria-expanded={esAbierto} onClick={() => setAbierto(esAbierto ? null : m.id)}>
                  <span className="event-title"><Icono size={16} aria-hidden="true" />{m.titulo}</span>
                  <span className="event-sub">{m.subtitulo}</span>
                  <span className="event-meta">
                    <span><strong>{m.fecha_label}</strong>, {m.hace}</span>
                    <EtiquetaFuente fuente={m.fuente} catalogo={catalogo} />
                  </span>
                  <ChevronDown size={18} className="event-chev" aria-hidden="true" />
                </button>
                <AnimatePresence initial={false}>
                  {esAbierto && (
                    <motion.div className="event-body" initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.22 }}>
                      {m.analitos.length > 0 && (
                        <table className="results">
                          <thead>
                            <tr>
                              <th scope="col">Examen</th>
                              <th scope="col">Resultado</th>
                              <th scope="col">Referencia</th>
                              <th scope="col"><span className="sr-only">Interpretación</span></th>
                            </tr>
                          </thead>
                          <tbody>
                            {m.analitos.map((a) => (
                              <tr key={a.nombre} className={a.bandera !== 'N' ? 'is-out' : ''}>
                                <th scope="row">{a.nombre}</th>
                                <td><strong>{String(a.valor).replace('.', ',')}</strong> {a.unidad}</td>
                                <td>{rango(m, a.nombre)}</td>
                                <td>
                                  {a.bandera === 'H' ? <span className="flag">Alto</span>
                                    : a.bandera === 'L' ? <span className="flag">Bajo</span>
                                      : <span className="flag flag-ok">Normal</span>}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                      {m.analitos.length === 0 && m.detalle.length > 0 && (
                        <dl className="detail">
                          {m.detalle.map(([k, v]) => (
                            <Fragment key={k}><dt>{k}</dt><dd>{v}</dd></Fragment>
                          ))}
                        </dl>
                      )}
                      <button className="link"
                        onClick={() => alInspeccionar(m.recursos.length === 1 ? m.recursos[0] : m.recursos)}>
                        <Braces size={14} aria-hidden="true" />
                        Ver recurso FHIR
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.li>
            )
          })}
          {items.length === 0 && (
            <li className="event-empty">Con el permiso que dio la paciente no hay eventos para mostrar.</li>
          )}
        </ol>
      </div>

      <aside className="today" aria-label="Atención de hoy">
        <h4>Atención de hoy</h4>
        <p className="today-meta">Urgencias, {fechaCorta(sim.ahora)}. Dolor abdominal y fiebre.</p>
        <label className="field">
          <span>Nota de la atención</span>
          <textarea rows={6} value={borrador.nota} onChange={(ev) => control.editarBorrador({ nota: ev.target.value })} />
        </label>
        <label className="field">
          <span>Dónde se registra la atención</span>
          <select value={borrador.destino}
            onChange={(ev) => control.editarBorrador({ destino: ev.target.value as 'hilo' | 'ips' })}>
            <option value="hilo">En Hilo Clínico</option>
            <option value="ips">En el sistema de la IPS</option>
          </select>
          {borrador.destino === 'ips' && <span className="field-help">Se envía por API FHIR a la clínica.</span>}
        </label>
        <button className="btn btn-primary btn-turn" onClick={() => registrar(sim, control)}>
          <Check size={18} aria-hidden="true" />
          Registrar atención
        </button>
      </aside>
    </motion.div>
  )
}
