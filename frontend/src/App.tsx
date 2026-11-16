import { useEffect, useState } from 'react'

// Pantalla temporal: solo comprueba que el frontend habla con el backend.
// Se reemplaza por las vistas del prototipo (Simulación, Proceso BPMN, Impacto).
export default function App() {
  const [estado, setEstado] = useState('consultando…')

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then((d) => setEstado(d.status))
      .catch(() => setEstado('sin conexión con el backend'))
  }, [])

  return (
    <main style={{ padding: 32 }}>
      <h1>Hilo Clínico</h1>
      <p>Backend: {estado}</p>
    </main>
  )
}
