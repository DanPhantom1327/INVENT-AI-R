import { useState } from 'react'
import './AnalysisDashboard.css'

const fmt = (value, digits = 1) => value == null || value === '' || !Number.isFinite(Number(value))
  ? '—'
  : Number(value).toLocaleString('es-CO', { maximumFractionDigits: digits })

const fmtCantidad = (value, tipo) => {
  const cantidad = asNumber(value)

  if (cantidad == null) return '—'

  if (tipo === 'PRODUCTO_TERMINADO') {
    return `${fmt(Math.ceil(Math.max(0, cantidad)), 0)} empaques`
  }

  return `${fmt(cantidad, 2)} kg`
}
const models = {
  promedio_estacional_4s: 'Promedio estacional (4 semanas)',
  regresion_tendencia_semanal: 'Regresión con tendencia semanal',
  regresion_log_tendencia_semanal: 'Regresión logarítmica semanal',
}
const asNumber = value => value == null || value === '' ? null : (Number.isFinite(Number(value)) ? Number(value) : null)
const status = (days, threshold) => {
  const c = asNumber(days), t = asNumber(threshold)
  if (c == null || t == null || t <= 0) return ['Sin evaluar', 'neutral']
  if (c < t * .5) return ['Alto', 'high']
  if (c < t) return ['Medio', 'medium']
  if (c < t * 1.25) return ['Bajo', 'low']
  return ['Sin riesgo inmediato', 'safe']
}

function ForecastBars({ rows, type }) {
  const selected = rows.filter(r => r.tipo === type && asNumber(r.proyeccion_total) != null)
  if (!selected.length) return <p className="ia-empty">Todavía no hay pronósticos para estos productos.</p>
  const max = Math.max(1, ...selected.map(r => Math.max(0, Number(r.proyeccion_total))))
  const unit = type === 'PRODUCTO_TERMINADO' ? 'empaques' : 'kg'
  return <div className="ia-bar-group">
    {selected.map(r => <div className="ia-bar-line" key={r.item_id}>
      <div className="ia-bar-head">
        <span>{r.nombre}</span>
        <strong>{fmtCantidad(r.proyeccion_total, r.tipo)}</strong>
      </div>
      <div className="ia-track"><div className="ia-fill" style={{ width: `${100 * Math.max(0, Number(r.proyeccion_total)) / max}%` }}/></div>
    </div>)}
  </div>
}

export default function AnalysisDashboard({ data = {}, errors = {}, user, api, refresh }) {
  const [pending, setPending] = useState('')
  const [notice, setNotice] = useState(null)
  const [horizon, setHorizon] = useState('14')
  const canCalculate = ['ADMIN', 'ANALISTA_DATOS'].includes(user?.rol)
  const forecasts = data.proyecciones || []
  const coverage = data.cobertura || []
  const alerts = (data.alertas || []).filter(a => a.estado === 'ACTIVA')
  const warnings = ['proyecciones', 'cobertura', 'alertas'].filter(k => errors[k])

  async function calculate(kind) {
    if (pending || !canCalculate) return
    setPending(kind)
    setNotice(null)
    try {
      const endpoint = kind === 'forecast' ? '/analisis/proyecciones/generar' : '/analisis/cobertura/calcular'
      const options = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(kind === 'forecast' ? { horizonte_dias: Number(horizon) } : {}),
      }
      const result = await api(endpoint, options)
      await refresh()
      const list = result?.resultados || []
      const issues = list.filter(x => x.estado && x.estado !== 'OK')
      setNotice({ error: false, text: `${kind === 'forecast' ? 'Proyecciones generadas' : 'Coberturas y alertas recalculadas'}: ${list.length} productos analizados.${issues.length ? ` ${issues.length} sin pronóstico completo.` : ''}` })
    } catch (e) {
      setNotice({ error: true, text: e.message || 'No se pudo completar el cálculo.' })
    } finally { setPending('') }
  }

  return <div className="ia-page">
    <section className="panel ia-intro">
      <div><h2>Inteligencia de inventarios</h2><p>Proyecciones de demanda, cobertura del stock y alertas, a partir del historial registrado.</p></div>
      {canCalculate && <div className="ia-controls">
        <label>Horizonte <select value={horizon} disabled={!!pending} onChange={e => setHorizon(e.target.value)}>
          <option value="7">7 días</option><option value="14">14 días</option><option value="30">30 días</option>
        </select></label>
        <button className="outline" disabled={!!pending} onClick={() => calculate('forecast')}>{pending === 'forecast' ? 'Calculando...' : 'Generar proyecciones'}</button>
        <button className="outline" disabled={!!pending} onClick={() => calculate('coverage')}>{pending === 'coverage' ? 'Calculando...' : 'Recalcular cobertura y alertas'}</button>
      </div>}
    </section>
    {notice && <div className={`notice ${notice.error ? 'error' : 'ia-success'}`} role="status">{notice.text}</div>}
    {warnings.length > 0 && <div className="notice warning">No se pudieron consultar todos los módulos: {warnings.map(k => `${k}: ${errors[k]}`).join(' · ')}</div>}
    <div className="ia-metrics">
      <div className="ia-metric"><span>Productos con proyección</span><strong>{data.proyecciones ? forecasts.length : '—'}</strong></div>
      <div className="ia-metric"><span>Coberturas registradas</span><strong>{data.cobertura ? coverage.length : '—'}</strong></div>
      <div className="ia-metric"><span>Alertas activas</span><strong>{data.alertas ? alerts.length : '—'}</strong></div>
    </div>
    <div className="ia-columns">
      <section className="panel"><div className="panel-heading"><div><h2>Demanda de pulpas empacadas</h2><p>Pronóstico total según el horizonte guardado · unidades de 230 g</p></div></div><ForecastBars rows={forecasts} type="PRODUCTO_TERMINADO"/></section>
      <section className="panel"><div className="panel-heading"><div><h2>Consumo de materia prima</h2><p>Pronóstico total de salidas de producción · kilogramos</p></div></div><ForecastBars rows={forecasts} type="MATERIA_PRIMA"/></section>
    </div>
    <section className="panel"><div className="panel-heading"><div><h2>Modelos y predicciones</h2><p>Último pronóstico guardado para cada producto; las cantidades son estimaciones estadísticas.</p></div></div>
      <div className="table-scroll"><table><thead><tr><th>Producto</th><th>Modelo seleccionado</th><th>Horizonte</th><th>Demanda estimada</th><th>Compra sugerida</th></tr></thead><tbody>
        {forecasts.map((r, i) => <tr key={r.item_id ?? i}><td>{r.nombre}</td><td>{models[r.modelo_usado] || r.modelo_usado || '—'}</td><td>{r.horizonte_dias ?? '—'} días</td><td>{fmtCantidad(r.proyeccion_total, r.tipo)}</td><td>{r.tipo === 'MATERIA_PRIMA' ? `${fmt(r.compra_sugerida, 2)} kg` : 'No aplica'}</td></tr>)}
      </tbody></table></div>{!forecasts.length && <p className="ia-empty">No hay proyecciones guardadas o no se pudieron consultar.</p>}
    </section>
    <section className="panel"><div className="panel-heading"><div><h2>Cobertura de stock</h2><p>Días estimados de inventario frente al consumo; última cobertura guardada por producto.</p></div></div>
      <div className="table-scroll"><table><thead><tr><th>Producto</th><th>Stock</th><th>Cobertura</th><th>Umbral</th><th>Estado</th></tr></thead><tbody>
        {coverage.map((r, i) => { const [label, tone] = status(r.cobertura_dias, r.umbral_dias); return <tr key={r.item_id ?? i}><td>{r.nombre}</td><td>{fmtCantidad(r.stock_actual, r.tipo)}</td><td>{fmt(r.cobertura_dias)} días</td><td>{r.umbral_dias ?? '—'} días</td><td><span className={`ia-status ${tone}`}>{label}</span></td></tr> })}
      </tbody></table></div>{!coverage.length && <p className="ia-empty">No hay coberturas calculadas o no se pudieron consultar.</p>}
    </section>
    <section className="panel"><div className="panel-heading"><div><h2>Alertas de desabastecimiento</h2><p>Solo alertas activas; se generan cuando la cobertura cae cerca o por debajo del umbral.</p></div></div>
      {alerts.length ? alerts.map(a => <div className="ia-alert" key={a.id}><span className={`ia-status ${a.nivel_severidad === 'ALTO' ? 'high' : a.nivel_severidad === 'MEDIO' ? 'medium' : 'low'}`}>{a.nivel_severidad}</span><div><strong>{a.item_nombre}</strong><p>{a.mensaje}</p></div></div>) : <p className="ia-empty">{data.alertas ? 'No hay alertas activas con la cobertura calculada. Esto no sustituye revisar la calidad y actualidad de los datos.' : 'No fue posible consultar las alertas.'}</p>}
    </section>
    <p className="ia-disclaimer">Entorno académico: el historial de negocio utilizado es sintético. Los pronósticos pueden estar basados en registros antiguos y no garantizan la demanda futura. La cobertura proyectada superior al horizonte puede aparecer sin fecha estimable de agotamiento.</p>
  </div>
}
