import { useState } from 'react'

export default function App() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [usuario, setUsuario] = useState(null)
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  async function iniciarSesion(evento) {
    evento.preventDefault()
    setError('')
    setCargando(true)

    try {
      const respuesta = await fetch('/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      })

      if (!respuesta.ok) {
        throw new Error('Usuario o contraseña incorrectos')
      }

      const perfil = await fetch('/auth/me', {
        credentials: 'include',
      })

      if (!perfil.ok) {
        throw new Error('No se pudo obtener la sesión')
      }

      const datos = await perfil.json()
      setUsuario(datos)
      setPassword('')
    } catch (err) {
      setError(err.message)
    } finally {
      setCargando(false)
    }
  }

  if (usuario) {
    return (
      <main>
        <h1>INVENT-AI-R</h1>
        <h2>Bienvenido, {usuario.nombre_completo}</h2>
        <p>Usuario: {usuario.username}</p>
        <p>Rol: {usuario.rol}</p>
        <p>Estado: Sesión iniciada correctamente</p>
      </main>
    )
  }

  return (
    <main>
      <h1>INVENT-AI-R</h1>
      <p>Sistema inteligente de gestión de inventarios</p>

      <form onSubmit={iniciarSesion}>
        <h2>Iniciar sesión</h2>

        <input
          placeholder="Usuario"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />

        <input
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button type="submit" disabled={cargando}>
          {cargando ? 'Ingresando...' : 'Ingresar'}
        </button>

        {error && <p role="alert">{error}</p>}
      </form>
    </main>
  )
}
