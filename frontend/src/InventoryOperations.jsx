import { useEffect, useState } from 'react'
import './InventoryOperations.css'

const initialMovement = { item_id: '', tipo_movimiento: 'ENTRADA', cantidad: '', referencia: '', efecto: 'SUMA', motivo_ajuste: 'MERMA' }
const initialItem = { tipo: 'MATERIA_PRIMA', nombre: '', unidad_medida: 'kg', umbral_dias_cobertura: '' }
const motives = ['MERMA', 'ERROR_CONTEO', 'DEVOLUCION']

export default function InventoryOperations({ items = [], user, api, refresh }) {
  const [tab, setTab] = useState('movimiento')
  const [movement, setMovement] = useState(initialMovement)
  const [item, setItem] = useState(initialItem)
  const [history, setHistory] = useState([])
  const [historyError, setHistoryError] = useState('')
  const [pending, setPending] = useState(false)
  const [notice, setNotice] = useState(null)
  const writable = ['ADMIN', 'LOGISTICO'].includes(user?.rol)

  async function loadHistory() {
    try {
      const data = await api('/inventario/movimientos')
      setHistory(Array.isArray(data) ? data.slice(0, 25) : Array.isArray(data?.results) ? data.results.slice(0, 25) : [])
      setHistoryError('')
    } catch (error) { setHistoryError(error.message || 'No fue posible cargar el historial') }
  }
  useEffect(() => { loadHistory() }, [])

  const chosen = items.find(it => String(it.id) === String(movement.item_id))
  const esPulpa = chosen?.tipo === 'PRODUCTO_TERMINADO'

  const cantidadValida = () => {
  const valor = String(movement.cantidad)
  const cantidad = Number(valor)

  if (!Number.isFinite(cantidad) || cantidad <= 0) {
    return false
    }

    if (esPulpa) {
      return /^[1-9]\d*$/.test(valor) &&
        Number.isSafeInteger(cantidad)
    }

    return /^\d+(?:\.\d{1,2})?$/.test(valor)
  }
  function changeMovement(key, value) { setMovement(old => ({ ...old, [key]: value })); setNotice(null) }
  function changeItem(key, value) { setItem(old => ({ ...old, [key]: value })); setNotice(null) }

  async function submitMovement(event) {
    event.preventDefault()
    if (pending || !writable) return
    const cantidad = Number(movement.cantidad)
    if (
      !chosen ||
      !cantidadValida() ||
      cantidad > 9999999999.99
    ) {
      setNotice({
        error: true,
        text: esPulpa
          ? 'La pulpa de 230g solo permite empaques completos (1, 2, 3...).'
          : 'Ingresa una cantidad válida en kg, con máximo dos decimales.',
      })
      return
    }
    const adjustment = movement.tipo_movimiento === 'AJUSTE'
    const subtract = adjustment ? movement.efecto === 'RESTA' : movement.tipo_movimiento === 'SALIDA'
    if (subtract && cantidad > Number(chosen.stock_actual)) {
      setNotice({ error: true, text: 'No hay suficiente stock para esta resta. Verifica las existencias antes de continuar.' }); return
    }
    const operation = adjustment ? `AJUSTE (${movement.efecto}, motivo: ${movement.motivo_ajuste})` : movement.tipo_movimiento
    if (!window.confirm(`Vas a registrar ${operation} de ${cantidad} ${chosen.unidad_medida} para «${chosen.nombre}». Esta operación modifica el stock real en PostgreSQL. ¿Confirmas?`)) return
    const payload = { item_id: Number(movement.item_id), cantidad: movement.cantidad, referencia: movement.referencia.trim() }
    if (adjustment) { payload.efecto = movement.efecto; payload.motivo_ajuste = movement.motivo_ajuste }
    else payload.tipo_movimiento = movement.tipo_movimiento
    setPending(true); setNotice(null)
    try {
      await api(adjustment ? '/inventario/movimientos/ajuste' : '/inventario/movimientos', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
      })
      setMovement(initialMovement)
      setNotice({ error: false, text: 'Movimiento registrado correctamente. Se actualizaron los datos de inventario.' })
      await Promise.allSettled([refresh(), loadHistory()])
    } catch (error) { setNotice({ error: true, text: error.message || 'No se pudo registrar el movimiento' }) }
    finally { setPending(false) }
  }

  async function submitItem(event) {
    event.preventDefault()
    if (pending || !writable) return
    const nombre = item.nombre.trim()
    if (!nombre || !item.unidad_medida.trim()) { setNotice({ error: true, text: 'Nombre y unidad de medida son obligatorios.' }); return }
    const payload = {
      tipo: item.tipo,
      nombre,
      unidad_medida:
        item.tipo === 'PRODUCTO_TERMINADO' ? 'unidad' : 'kg',
    }
    if (item.umbral_dias_cobertura !== '') {
      if (!/^\d+$/.test(String(item.umbral_dias_cobertura))) { setNotice({ error: true, text: 'El umbral debe ser un número entero no negativo.' }); return }
      payload.umbral_dias_cobertura = Number(item.umbral_dias_cobertura)
    }
    if (!window.confirm(`Crearás el ítem «${nombre}» (${item.tipo}). ¿Confirmas?`)) return
    setPending(true); setNotice(null)
    try {
      await api('/inventario/items', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      setItem(initialItem)
      setNotice({ error: false, text: 'Ítem creado correctamente. Ya aparece en el listado de inventario.' })
      await refresh()
    } catch (error) { setNotice({ error: true, text: error.message || 'No se pudo crear el ítem' }) }
    finally { setPending(false) }
  }

  return <section className="panel inv-operations">
    <div className="panel-heading"><div><h2>Operaciones de inventario</h2><p>Acciones registradas en PostgreSQL a través de Django</p></div><span className="inv-permission">{writable ? 'Edición habilitada' : 'Solo lectura'}</span></div>
    {writable && <>
      <div className="inv-tabs"><button type="button" className={tab === 'movimiento' ? 'selected' : ''} onClick={() => { setTab('movimiento'); setNotice(null) }}>Entrada / Salida / Ajuste</button><button type="button" className={tab === 'item' ? 'selected' : ''} onClick={() => { setTab('item'); setNotice(null) }}>Crear ítem</button></div>
      {tab === 'movimiento' ? <form className="inv-form" onSubmit={submitMovement}>
        <label>Producto o materia prima<select required value={movement.item_id} onChange={e => {
  setMovement(old => ({
    ...old,
    item_id: e.target.value,
    cantidad: '',
  }))
  setNotice(null)
}}><option value="">Selecciona un ítem...</option>{items.map(it => <option key={it.id} value={it.id}>{it.nombre} — {Number(it.stock_actual).toLocaleString('es-CO')} {it.unidad_medida}</option>)}</select></label>
        <label>Operación<select value={movement.tipo_movimiento} onChange={e => changeMovement('tipo_movimiento', e.target.value)}><option value="ENTRADA">Entrada (+ stock)</option><option value="SALIDA">Salida (− stock)</option><option value="AJUSTE">Ajuste de inventario</option></select></label>
        <label>
          {esPulpa
            ? 'Cantidad de empaques de 230g'
            : 'Cantidad en kilogramos (kg)'}

          <input
            type="number"
            min={esPulpa ? '1' : '0.01'}
            step={esPulpa ? '1' : '0.01'}
            required
            value={movement.cantidad}
            onChange={e =>
              changeMovement('cantidad', e.target.value)
            }
            placeholder={esPulpa ? 'Ej. 5' : 'Ej. 10.50'}
          />
        </label>
        {movement.tipo_movimiento === 'AJUSTE' && <><label>Efecto<select value={movement.efecto} onChange={e => changeMovement('efecto', e.target.value)}><option value="SUMA">SUMA (+ stock)</option><option value="RESTA">RESTA (− stock)</option></select></label><label>Motivo del ajuste<select value={movement.motivo_ajuste} onChange={e => changeMovement('motivo_ajuste', e.target.value)}>{motives.map(m => <option key={m} value={m}>{m.replaceAll('_', ' ')}</option>)}</select></label></>}
        <label>Referencia (opcional)<input maxLength={100} value={movement.referencia} onChange={e => changeMovement('referencia', e.target.value)} placeholder="Ej. prueba de inventario"/></label>
        <div className="inv-actions"><span>{chosen ? `Stock actual: ${Number(chosen.stock_actual).toLocaleString('es-CO')} ${chosen.unidad_medida}` : 'Selecciona un ítem para ver sus existencias.'}</span><button type="submit" className="primary" disabled={pending || !items.length}>{pending ? 'Guardando...' : 'Confirmar movimiento'}</button></div>
      </form> : <form className="inv-form" onSubmit={submitItem}>
        <label>Tipo<select value={item.tipo} onChange={e => changeItem('tipo', e.target.value)}><option value="MATERIA_PRIMA">Materia prima</option><option value="PRODUCTO_TERMINADO">Producto terminado</option></select></label>
        <label>Nombre<input maxLength={150} required value={item.nombre} onChange={e => changeItem('nombre', e.target.value)} placeholder="Ej. Piña fresca"/></label>
        <label>Unidad de medida<input maxLength={20} required value={item.unidad_medida} onChange={e => changeItem('unidad_medida', e.target.value)} placeholder="kg"/></label>
        <label>Umbral de cobertura (días, opcional)<input type="number" min="0" step="1" value={item.umbral_dias_cobertura} onChange={e => changeItem('umbral_dias_cobertura', e.target.value)}/></label>
        <div className="inv-actions"><span>La creación no registra stock inicial. Para añadir existencias usa una entrada.</span><button type="submit" className="primary" disabled={pending}>{pending ? 'Guardando...' : 'Crear ítem'}</button></div>
      </form>}
    </>}
    {!writable && <p className="inv-readonly">Tu rol puede consultar inventario y movimientos, pero no registrar operaciones.</p>}
    {notice && <div role="status" className={`notice ${notice.error ? 'error' : 'inv-success'}`}>{notice.text}</div>}
    <div className="inv-history-head"><div><h3>Últimos movimientos</h3><p>Hasta 25 registros recientes</p></div><button type="button" className="outline" onClick={loadHistory}>↻ Actualizar historial</button></div>
    {historyError && <div className="notice error">{historyError}</div>}
    <div className="table-scroll"><table><thead><tr><th>Fecha</th><th>Ítem</th><th>Tipo</th><th>Efecto</th><th>Cantidad</th><th>Referencia</th></tr></thead><tbody>{history.map(m => <tr key={m.id}><td>{m.fecha ? new Date(m.fecha).toLocaleString('es-CO') : '—'}</td><td>{items.find(i => String(i.id) === String(m.item))?.nombre || `#${m.item}`}</td><td>{m.tipo_movimiento}</td><td>{m.efecto}</td><td>{m.cantidad}</td><td>{m.referencia || '—'}</td></tr>)}</tbody></table>{!history.length && !historyError && <p className="inv-readonly">No hay movimientos disponibles.</p>}</div>
  </section>
}
