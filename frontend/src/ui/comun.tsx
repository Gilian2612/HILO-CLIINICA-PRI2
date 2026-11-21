// Piezas compartidas por las vistas (equivalen a Cr, Bp, Bn y Zt del boceto).
import type { ReactNode } from 'react'
import { motion } from 'framer-motion'
import type { Catalogo, FuenteId } from '../api'

/** Colores fijos de cada fuente (también vienen en el catálogo; aquí para el primer pintado). */
const COLOR: Record<FuenteId, string> = { eps: '#C27A1E', ips: '#5B6FD6', lab: '#1F9A7A' }

/** Entrada y salida suaves de cada pantalla. */
export const aparecer = {
  initial: { opacity: 0, y: 6 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -4 },
  transition: { duration: 0.22, ease: 'easeOut' },
} as const

/** Nudo de la fuente: rombo (EPS), círculo (IPS), cuadrado (laboratorio). */
export function Nudo({ fuente, size = 14, title }: { fuente: FuenteId; size?: number; title?: string }) {
  const r = size / 2
  const color = COLOR[fuente]
  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className="knot"
      role={title ? 'img' : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
    >
      {fuente === 'eps' && <path d={`M${r} 0.8 L${size - 0.8} ${r} L${r} ${size - 0.8} L0.8 ${r} Z`} fill={color} />}
      {fuente === 'ips' && <circle cx={r} cy={r} r={r - 1} fill={color} />}
      {fuente === 'lab' && <rect x="1.5" y="1.5" width={size - 3} height={size - 3} rx="2.5" fill={color} />}
    </svg>
  )
}

export function EtiquetaFuente({ fuente, catalogo }: { fuente: FuenteId; catalogo: Catalogo }) {
  return (
    <span className="source-tag">
      <Nudo fuente={fuente} size={11} />
      {fuenteDe(catalogo, fuente).nombre}
    </span>
  )
}

export function fuenteDe(catalogo: Catalogo, id: FuenteId) {
  return catalogo.fuentes.find((f) => f.id === id)!
}

/** Aviso grande del visor (esperando, acceso abierto, guardando, cerrado…). */
export function Aviso({
  icono,
  titulo,
  texto,
  tono = 'info',
  ocupado,
  children,
}: {
  icono: ReactNode
  titulo: string
  texto: string
  tono?: 'info' | 'lock' | 'ok'
  ocupado?: boolean
  children?: ReactNode
}) {
  return (
    <motion.div className={`notice notice-${tono}`} {...aparecer} role="status">
      <span className={`notice-icon ${ocupado ? 'is-busy' : ''}`} aria-hidden="true">
        {icono}
      </span>
      <h3>{titulo}</h3>
      <p>{texto}</p>
      {children && <div className="notice-actions">{children}</div>}
    </motion.div>
  )
}

// ---------- Formatos de presentación ----------

/** "22:41:07" en hora de Colombia. */
export const horaColombia = (iso: string) =>
  new Date(iso).toLocaleTimeString('es-CO', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone: 'America/Bogota',
  })

const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

/** "14 nov 2026" a partir de la fecha local de un ISO con zona. */
export const fechaCorta = (iso: string) => {
  const [a, m, d] = iso.slice(0, 10).split('-').map(Number)
  return `${d} ${MESES[m - 1]} ${a}`
}

/** Edad cumplida en la fecha `hoy` (ambas ISO). */
export const edad = (nacimiento: string, hoy: string) => {
  const [a, m, d] = nacimiento.slice(0, 10).split('-').map(Number)
  const [ha, hm, hd] = hoy.slice(0, 10).split('-').map(Number)
  return ha - a - (hm < m || (hm === m && hd < d) ? 1 : 0)
}
