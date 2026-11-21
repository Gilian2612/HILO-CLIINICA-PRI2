import { WORDMARK } from './wordmarkPath'

export function Wordmark({ className = '' }: { className?: string }) {
  return (
    <svg className={`wordmark ${className}`} viewBox={WORDMARK.viewBox} role="img" aria-label="Hilo Clínico">
      <path d={WORDMARK.d} fill="currentColor" />
    </svg>
  )
}
