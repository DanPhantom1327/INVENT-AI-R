import { useEffect, useMemo, useState } from 'react'
import './App.css'
import InventoryOperations from './InventoryOperations'
import CommercialOperations from './CommercialOperations'
import AnalysisDashboard from './AnalysisDashboard'

const MENU = [
  ['dashboard', '▦', 'Resumen general'],
  ['inventario', '▤', 'Inventarios'],
  ['ventas', '↗', 'Ventas'],
  ['compras', '↙', 'Compras'],
  ['analisis', '◈', 'Análisis e IA'],
]
const ENDPOINTS = {
  items: '/inventario/items',
  ventas: '/ventas',
  compras: '/compras',
  alertas: '/analisis/alertas',
  cobertura: '/analisis/cobertura',
  proyecciones: '/analisis/proyecciones',
}

async function api(url, options = {}, retry = true) {
  const response = await fetch(url, { credentials: 'include', ...options })
  if (response.status === 401 && retry && !url.includes('/auth/')) {
    const refresh = await fetch('/auth/refresh', { method: 'POST', credentials: 'include' })
    if (refresh.ok) return api(url, options, false)
  }
  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try { const body = await response.json(); detail = body.detail || detail } catch { /* keep HTTP error */ }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  if (response.status === 204) return null
  return response.json()
}
const asList = data => Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : []
const number = value => Number(value || 0).toLocaleString('es-CO', { maximumFractionDigits: 2 })
const pesos = value => Number(value || 0).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
const date = value => value ? new Date(value).toLocaleDateString('es-CO') : '—'
const texto = value => value == null || value === '' ? '—' : String(value)

export default function App() {
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [loginLoading, setLoginLoading] = useState(false)
  const [section, setSection] = useState('dashboard')
  const [data, setData] = useState({})
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let active = true
    async function restore() {
      try {
        let me
        try { me = await api('/auth/me') }
        catch {
          await api('/auth/refresh', { method: 'POST' }, false)
          me = await api('/auth/me')
        }
        if (active) setUser(me)
      } catch { if (active) setUser(null) }
      finally { if (active) setAuthLoading(false) }
    }
    restore()
    return () => { active = false }
  }, [])

  async function loadData() {
    setLoading(true)
    const values = await Promise.allSettled(Object.entries(ENDPOINTS).map(async ([key, url]) => [key, await api(url)]))
    const nextData = {}, nextErrors = {}
    values.forEach((result, index) => {
      const key = Object.keys(ENDPOINTS)[index]
      if (result.status === 'fulfilled') nextData[key] = asList(result.value[1])
      else nextErrors[key] = result.reason?.message || 'No se pudo conectar'
    })
    setData(nextData); setErrors(nextErrors); setLoading(false)
  }

  useEffect(() => { if (user) loadData() }, [user])

  async function login(event) {
    event.preventDefault(); setLoginError(''); setLoginLoading(true)
    try {
      await api('/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) }, false)
      const me = await api('/auth/me')
      setUser(me); setPassword('')
    } catch (err) { setLoginError(err.message || 'No se pudo iniciar sesión') }
    finally { setLoginLoading(false) }
  }

  async function logout() {
    try { await api('/auth/logout', { method: 'POST' }, false) } catch { /* clear local view even on network error */ }
    setUser(null); setData({}); setSection('dashboard')
  }

  const totals = useMemo(() => ({
    items: data.items?.length,
    stock: data.items?.reduce((sum, item) => sum + Number(item.stock_actual || 0), 0),
    ventas: data.ventas?.length,
    importeVentas: data.ventas?.reduce((sum, sale) => sum + Number(sale.total || 0), 0),
    compras: data.compras?.length,
    importeCompras: data.compras?.reduce((sum, purchase) => sum + Number(purchase.total || 0), 0),
    alertas: data.alertas?.filter(alert => String(alert.estado || '').toUpperCase() !== 'RESUELTA').length,
  }), [data])

  if (authLoading) return <div className="screen-center">Verificando sesión...</div>
  if (!user) return <div className="login-layout"><section className="login-brand"><div className="mark">◈</div><span className="eyebrow">CONTROL INTELIGENTE DE INVENTARIOS</span><h1>INVENT<span>·AI·R</span></h1><p>Controla tu stock. Analiza el historial. Anticipa la demanda.</p><div className="login-accent">Inventarios · Compras · Ventas · Inteligencia artificial</div></section><form className="login-card" onSubmit={login}><span className="eyebrow">BIENVENIDO</span><h2>Iniciar sesión</h2><p>Ingresa con tus credenciales asignadas.</p><label>Usuario<input value={username} onChange={e => setUsername(e.target.value)} placeholder="Nombre de usuario" required autoComplete="username" /></label><label>Contraseña<input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Tu contraseña" required autoComplete="current-password" /></label>{loginError && <div className="notice error" role="alert">{loginError}</div>}<button className="primary" disabled={loginLoading}>{loginLoading ? 'Verificando...' : 'Ingresar al sistema →'}</button></form></div>

  const missing = Object.keys(errors).length > 0
  const rows = section === 'inventario' ? data.items : section === 'ventas' ? data.ventas : section === 'compras' ? data.compras : section === 'analisis' ? data.proyecciones : []
  const columns = {
    inventario: [['id','ID'],['nombre','Producto / materia prima'],['tipo','Tipo'],['stock_actual','Stock'],['unidad_medida','Unidad'],['activo','Activo']],
    ventas: [['id','ID'],['producto_id','Producto ID'],['cantidad','Cantidad'],['total','Total COP'],['fecha','Fecha']],
    compras: [['id','ID'],['materia_prima_id','Materia prima ID'],['proveedor','Proveedor'],['cantidad','Cantidad'],['total','Total COP'],['fecha','Fecha']],
    analisis: [['nombre','Producto'],['modelo_usado','Modelo'],['horizonte_dias','Horizonte (días)'],['proyeccion_total','Demanda proyectada'],['compra_sugerida','Compra sugerida']],
  }
  const formatCell = (key, value) => key === 'fecha' ? date(value) : key === 'total' ? pesos(value) : key === 'activo' ? (value ? 'Sí' : 'No') : texto(value)

  return <div className="app-shell">
    <aside className="sidebar"><div className="sidebar-brand"><div className="mark small">◈</div><div><strong>INVENT<span>·AI·R</span></strong><small>GESTIÓN INTELIGENTE</small></div></div><p className="menu-label">MENÚ PRINCIPAL</p><nav>{MENU.map(([id, symbol, label]) => <button key={id} className={`nav-item ${section === id ? 'active' : ''}`} onClick={() => setSection(id)}><span>{symbol}</span>{label}</button>)}</nav><div className="sidebar-bottom"><span className="live-dot"/> Sistema de desarrollo <small>Backend Django + PostgreSQL</small></div></aside>
    <div className="workspace"><header className="topbar"><span className="breadcrumb">INVENT-AI-R <b>/</b> {MENU.find(item => item[0] === section)?.[2]}</span><div className="user-actions"><span className="user-dot">{(user.nombre_completo || user.username || 'A').slice(0,1).toUpperCase()}</span><div className="user-text"><strong>{user.nombre_completo || user.username}</strong><small>{user.rol}</small></div><button className="outline" onClick={logout}>Cerrar sesión</button></div></header>
      <main className="content"><div className="page-heading"><div><div className="eyebrow">PANEL DE CONTROL / {new Date().toLocaleDateString('es-CO')}</div><h1>{section === 'dashboard' ? 'Resumen general' : MENU.find(item => item[0] === section)?.[2]}</h1><p>{section === 'dashboard' ? 'Una vista centralizada del estado de tu operación.' : 'Información consultada directamente desde los microservicios.'}</p></div><button className="outline refresh" disabled={loading} onClick={loadData}>{loading ? 'Actualizando...' : '↻ Actualizar datos'}</button></div>
      {missing && <div className="notice warning" role="status"><b>Algunos servicios no respondieron.</b> Los datos ausentes se muestran como «Sin datos», nunca como cero. <details><summary>Ver detalles</summary>{Object.entries(errors).map(([k, e]) => <p key={k}>{k}: {e}</p>)}</details></div>}
      {section === 'analisis' ? <AnalysisDashboard data={data} errors={errors} user={user} api={api} refresh={loadData} /> : section === 'dashboard' ? <><div className="stats-grid"><Metric icon="▤" title="Ítems de inventario" value={totals.items == null ? 'Sin datos' : number(totals.items)} foot="Materias primas y productos"/><Metric icon="↗" title="Ventas registradas" value={totals.ventas == null ? 'Sin datos' : number(totals.ventas)} foot={totals.importeVentas == null ? 'Sin datos de ventas' : `${pesos(totals.importeVentas)} acumulados`}/><Metric icon="↙" title="Compras registradas" value={totals.compras == null ? 'Sin datos' : number(totals.compras)} foot={totals.importeCompras == null ? 'Sin datos de compras' : `${pesos(totals.importeCompras)} acumulados`}/><Metric icon="!" title="Alertas no resueltas" value={totals.alertas == null ? 'Sin datos' : number(totals.alertas)} foot="Según el servicio de análisis"/></div><div className="panel-grid"><section className="panel"><div className="panel-heading"><div><h2>Existencias actuales</h2><p>Stock por ítem registrado</p></div><button className="text-link" onClick={() => setSection('inventario')}>Ver inventarios →</button></div>{data.items?.length ? <div className="stock-list">{data.items.slice(0,8).map(item => <div className="stock-row" key={item.id}><div><strong>{item.nombre}</strong><small>{item.tipo?.replaceAll('_', ' ')}</small></div><span>{number(item.stock_actual)} <small>{item.unidad_medida}</small></span></div>)}</div> : <Empty label="No hay datos de inventario disponibles"/>}</section><section className="panel"><div className="panel-heading"><div><h2>Alertas de inventario</h2><p>Notificaciones del módulo de análisis</p></div><button className="text-link" onClick={() => setSection('analisis')}>Ver análisis →</button></div>{data.alertas?.length ? <div className="alerts">{data.alertas.slice(0,7).map((alert, index) => <div className="alert-row" key={alert.id || index}><span className="alert-icon">!</span><div><strong>{alert.item_nombre || 'Ítem de inventario'}</strong><p>{alert.mensaje}</p><small>{alert.nivel_severidad} · {alert.estado}</small></div></div>)}</div> : <Empty label="No hay alertas disponibles"/>}</section></div><div className="footer-note">Los indicadores corresponden a todos los registros devueltos por las APIs, no exclusivamente al mes actual. Los datos provienen de PostgreSQL; para esta demostración se utiliza un historial sintético.</div></> : <section className="panel table-panel"><div className="panel-heading"><div><h2>Registros de {section === 'analisis' ? 'proyecciones' : section}</h2><p>{rows ? `${rows.length} registros recibidos` : 'Servicio no disponible'}</p></div></div>{rows?.length ? <div className="table-scroll"><table><thead><tr>{columns[section].map(([key, label]) => <th key={key}>{label}</th>)}</tr></thead><tbody>{rows.slice(0,100).map((item, index) => <tr key={item.id ?? item.item_id ?? index}>{columns[section].map(([key]) => <td key={key}>{formatCell(key, item[key])}</td>)}</tr>)}</tbody></table>{rows.length > 100 && <div className="footer-note">Mostrando los primeros 100 registros.</div>}</div> : <Empty label={errors[section] || errors[section === 'inventario' ? 'items' : section === 'analisis' ? 'proyecciones' : section] ? 'No se pudo consultar este servicio' : 'Aún no hay registros disponibles'}/>}</section>}
      {section === 'inventario' && <InventoryOperations items={data.items || []} user={user} api={api} refresh={loadData} />}
      {(section === 'ventas' || section === 'compras') && <CommercialOperations key={section} kind={section} items={data.items || []} user={user} api={api} refresh={loadData} />}
      </main></div>
  </div>
}
function Metric({ icon, title, value, foot }) { return <div className="metric"><div className="metric-icon">{icon}</div><div className="metric-label">{title}</div><div className="metric-value">{value}</div><div className="metric-foot">{foot}</div></div> }
function Empty({ label }) { return <div className="empty">{label}</div> }
