// App de la paciente en el teléfono (Op, XL y Z1 en el boceto).
import { AnimatePresence, motion } from 'framer-motion'
import { Ban, CircleCheck, Eye, Lock, ShieldCheck, Siren, X } from 'lucide-react'
import type { Catalogo, EventoAuditoria, Simulacion } from '../../api'
import type { ControlSimulacion } from '../../useSimulacion'
import avatarPaciente from '../../assets/avatar-paciente.svg'
import { Wordmark } from '../Wordmark'
import { Nudo, aparecer, fuenteDe, horaColombia } from '../comun'

type Pantalla = 'home' | 'request' | 'active' | 'emergency' | 'denied' | 'revoked' | 'done'

function pantalla(sim: Simulacion): Pantalla {
  const { ctx } = sim
  if (ctx.revocado) return 'revoked'
  if (sim.nodo === 'end_ok') return 'done'
  if (ctx.decision === 'denied') return 'denied'
  if (ctx.consent?.status === 'active') return ctx.emergencia ? 'emergency' : 'active'
  if (sim.nodo === 't_resp' && sim.estado === 'waiting') return 'request'
  return 'home'
}

export function Telefono({ sim, catalogo, control }: { sim: Simulacion; catalogo: Catalogo; control: ControlSimulacion }) {
  const p = pantalla(sim)
  const { medico } = sim
  const nombre = sim.ctx.mpi?.paciente.nombres.split(' ')[0] ?? 'Mariana'
  const consultas = sim.ctx.auditoria.filter((a) => a.accion.startsWith('Consulta a') && a.resultado === 'ok')

  return (
    <section className={`phone-wrap ${p === 'request' ? 'has-turn' : ''}`} aria-label="App de la paciente">
      <div className="phone">
        <div className="phone-status" aria-hidden="true">
          <span>10:41</span>
          <span className="phone-island" />
          <span>5G</span>
        </div>
        <header className="phone-head">
          <Wordmark />
          <span className="avatar avatar-paciente" aria-hidden="true">
            <img src={avatarPaciente} alt="" />
          </span>
        </header>
        <div className="phone-body">
          <AnimatePresence mode="wait" initial={false}>
            {p === 'home' && (
              <motion.div key="home" className="p-screen" {...aparecer}>
                <h3 className="p-hello">Hola, {nombre}</h3>
                <p className="p-lead">Tu historia clínica está repartida en tres lugares. Tú decides quién puede unirla.</p>
                <ul className="p-sources">
                  {(['eps', 'ips', 'lab'] as const).map((id) => (
                    <li key={id}>
                      <Nudo fuente={id} size={14} />
                      <div>
                        <strong>{fuenteDe(catalogo, id).nombre}</strong>
                        <span>{fuenteDe(catalogo, id).tipo}</span>
                      </div>
                    </li>
                  ))}
                </ul>
                <div className="p-empty">
                  <Eye size={18} aria-hidden="true" />
                  <span>Nadie ha consultado tu historia. Cuando un médico lo pida, te preguntamos aquí.</span>
                </div>
              </motion.div>
            )}
            {p === 'request' && <Solicitud key="request" sim={sim} catalogo={catalogo} control={control} />}
            {p === 'active' && (
              <motion.div key="active" className="p-screen" {...aparecer}>
                <div className="p-state p-state-ok">
                  <ShieldCheck size={20} aria-hidden="true" />
                  <div>
                    <strong>Acceso activo</strong>
                    <span>Vence mañana a las 10:41 p. m.</span>
                  </div>
                </div>
                <p className="p-lead">{medico.nombre} puede ver lo que autorizaste, en {medico.organizacion}.</p>
                <Registro items={consultas} />
                <button className="btn btn-danger" onClick={control.revocar}>
                  <X size={18} aria-hidden="true" />
                  Revocar acceso
                </button>
              </motion.div>
            )}
            {p === 'emergency' && (
              <motion.div key="emergency" className="p-screen" {...aparecer}>
                <div className="p-state p-state-warn">
                  <Siren size={20} aria-hidden="true" />
                  <div>
                    <strong>Acceso de emergencia</strong>
                    <span>Hoy, 10:41 p. m.</span>
                  </div>
                </div>
                <p className="p-lead">
                  {medico.nombre} abrió tu historia sin tu autorización porque registró una urgencia vital en{' '}
                  {medico.organizacion}. Quedó auditado a su nombre.
                </p>
                <Registro items={consultas} />
                <button className="btn btn-danger" onClick={control.revocar}>
                  <X size={18} aria-hidden="true" />
                  Cerrar el acceso ahora
                </button>
              </motion.div>
            )}
            {p === 'denied' && (
              <motion.div key="denied" className="p-screen" {...aparecer}>
                <div className="p-state p-state-lock">
                  <Ban size={20} aria-hidden="true" />
                  <div>
                    <strong>No autorizaste el acceso</strong>
                    <span>Hoy, 10:41 p. m.</span>
                  </div>
                </div>
                <p className="p-lead">Nadie vio tu historia. Si cambias de opinión, el médico puede volver a pedir permiso.</p>
              </motion.div>
            )}
            {p === 'revoked' && (
              <motion.div key="revoked" className="p-screen" {...aparecer}>
                <div className="p-state p-state-lock">
                  <Lock size={20} aria-hidden="true" />
                  <div>
                    <strong>Acceso revocado</strong>
                    <span>Tu historia volvió a estar cerrada</span>
                  </div>
                </div>
                <p className="p-lead">Esto fue lo que alcanzó a consultar {medico.nombre}:</p>
                <Registro items={consultas} />
              </motion.div>
            )}
            {p === 'done' && (
              <motion.div key="done" className="p-screen" {...aparecer}>
                <div className="p-state p-state-ok">
                  <CircleCheck size={20} aria-hidden="true" />
                  <div>
                    <strong>Tu atención quedó en tu hilo</strong>
                    <span>Urgencias, {medico.organizacion}</span>
                  </div>
                </div>
                <p className="p-lead">Tu próximo médico verá esta atención sin que tengas que llevar papeles.</p>
                <Registro items={consultas} titulo="Quién vio tu historia hoy" />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </section>
  )
}

function Registro({ items, titulo = 'Qué se ha consultado' }: { items: EventoAuditoria[]; titulo?: string }) {
  return (
    <div className="p-log">
      <h4>{titulo}</h4>
      {items.length === 0 ? (
        <p className="p-log-empty">Todavía nada. Cada consulta aparecerá aquí.</p>
      ) : (
        <ul>
          {items.map((a) => (
            <motion.li key={a.id + a.accion} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}>
              <span>{a.accion.replace('Consulta a ', '')}</span>
              <span className="p-log-time">{horaColombia(a.hora)}</span>
            </motion.li>
          ))}
        </ul>
      )}
    </div>
  )
}

function Solicitud({ sim, catalogo, control }: { sim: Simulacion; catalogo: Catalogo; control: ControlSimulacion }) {
  const { categorias } = sim.ctx.borrador
  const { medico } = sim
  const alternar = (id: string) =>
    control.editarBorrador({
      categorias: categorias.includes(id) ? categorias.filter((c) => c !== id) : [...categorias, id],
    })
  const ninguna = categorias.length === 0

  return (
    <motion.div className="p-screen p-request" initial={{ y: 40, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
      exit={{ y: 20, opacity: 0 }} transition={{ type: 'spring', stiffness: 320, damping: 30 }}>
      <p className="p-req-who"><strong>{medico.nombre}</strong> quiere ver tu historia clínica</p>
      <p className="p-req-where">{medico.rol} en {medico.organizacion}, {medico.ciudad}. Ahora mismo.</p>
      <fieldset className="p-scopes">
        <legend>Qué podrá ver durante 24 horas</legend>
        {catalogo.categorias.map((c) => (
          <label key={c.id} className="check">
            <input type="checkbox" checked={categorias.includes(c.id)} onChange={() => alternar(c.id)} />
            <span>{c.etiqueta}</span>
          </label>
        ))}
      </fieldset>
      {ninguna && <p className="field-error" role="alert">Elige al menos un tipo de información o no autorices.</p>}
      <div className="p-actions">
        <button className="btn btn-primary btn-turn" disabled={ninguna}
          onClick={() => control.actuar({ decision: 'granted', categorias })}>
          Autorizar acceso
        </button>
        <button className="btn btn-ghost" onClick={() => control.actuar({ decision: 'denied' })}>No autorizar</button>
      </div>
    </motion.div>
  )
}
