
import { useMemo, useRef, useState } from 'react'
import './CommercialOperations.css'

const ROLES = {
  ventas: ['ADMIN', 'VENDEDOR'],
  compras: ['ADMIN', 'ANALISTA_COMPRAS'],
}

const PRECIO_PULPA = 2800
const KG_POR_LIBRA = 0.5
const DECIMAL = /^\d{1,10}(?:\.\d{1,2})?$/
const ENTERO = /^[1-9]\d*$/

const money = n =>
  Number(n).toLocaleString('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 2,
  })

const formato = n =>
  Number(n).toLocaleString('es-CO', {
    maximumFractionDigits: 2,
  })

export default function CommercialOperations({
  kind,
  items = [],
  user,
  api,
  refresh,
}) {
  const isSale = kind === 'ventas'
  const allowed = ROLES[kind]?.includes(user?.rol) ?? false

  const [itemId, setItemId] = useState('')
  const [cantidad, setCantidad] = useState('')
  const [precio, setPrecio] = useState('')
  const [unidadCompra, setUnidadCompra] = useState('kg')
  const [proveedor, setProveedor] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState(null)

  const busyRef = useRef(false)

  const choices = useMemo(
    () =>
      items.filter(
        item =>
          item.activo !== false &&
          item.tipo === (
            isSale ? 'PRODUCTO_TERMINADO' : 'MATERIA_PRIMA'
          )
      ),
    [items, isSale]
  )

  const selected = choices.find(
    item => String(item.id) === String(itemId)
  )

  const cantidadValida = isSale
    ? ENTERO.test(cantidad) && Number.isSafeInteger(Number(cantidad))
    : DECIMAL.test(cantidad) && Number(cantidad) > 0

  const precioValido = isSale
    ? true
    : DECIMAL.test(precio) && Number(precio) >= 0

  const cantidadKg = !isSale && unidadCompra === 'lb'
    ? Number(cantidad) * KG_POR_LIBRA
    : Number(cantidad)

  const cantidadStock = isSale
    ? Number(cantidad)
    : cantidadKg

  const precioFinal = isSale
    ? PRECIO_PULPA
    : Number(precio)

  const total = cantidadStock * precioFinal

  const stockActual = Number(selected?.stock_actual ?? 0)

  const stockPosterior = isSale
    ? stockActual - cantidadStock
    : stockActual + cantidadStock

  function update(setter) {
    return event => {
      setter(event.target.value)
      setMessage(null)
    }
  }

  async function submit(event) {
    event.preventDefault()

    if (!allowed || busyRef.current) return

    if (!selected) {
      setMessage({
        error: true,
        text: 'Selecciona un producto válido.',
      })
      return
    }

    if (!cantidadValida || !precioValido ||
        cantidadStock <= 0 ||
        !Number.isFinite(total) ||
        !Number.isFinite(cantidadStock)) {
      setMessage({
        error: true,
        text: isSale
          ? 'La venta requiere un número entero de empaques.'
          : 'Revisa la cantidad y el precio de compra.',
      })
      return
    }

    if (isSale && cantidadStock > stockActual) {
      setMessage({
        error: true,
        text: 'No hay suficientes empaques disponibles.',
      })
      return
    }

    if (!isSale && (
      !proveedor.trim() || proveedor.trim().length > 150
    )) {
      setMessage({
        error: true,
        text: 'Ingresa un proveedor válido.',
      })
      return
    }

    const descripcion = isSale
      ? `${cantidadStock} empaques de ${selected.nombre}`
      : `${cantidad} ${unidadCompra} de ${selected.nombre}`

    const detalle = !isSale && unidadCompra === 'lb'
      ? ` (${formato(cantidadKg)} kg registrados)`
      : ''

    const confirmado = window.confirm(
      `¿Confirmas esta operación?\n\n` +
      `${isSale ? 'VENTA' : 'COMPRA'}\n` +
      `${descripcion}${detalle}\n` +
      `Total: ${money(total)}\n\n` +
      `Stock actual: ${formato(stockActual)} ${selected.unidad_medida}\n` +
      `Stock posterior estimado: ${formato(stockPosterior)} ${selected.unidad_medida}\n\n` +
      `Esta operación modificará PostgreSQL.`
    )

    if (!confirmado) return

    const body = isSale
      ? {
          producto_id: selected.id,
          cantidad: cantidadStock,
          precio_unitario: PRECIO_PULPA,
        }
      : {
          materia_prima_id: selected.id,
          cantidad: Number(cantidadKg.toFixed(2)),
          precio_unitario: precioFinal,
          proveedor: proveedor.trim(),
        }

    busyRef.current = true
    setBusy(true)
    setMessage(null)

    try {
      const result = await api(
        isSale ? '/ventas' : '/compras',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(body),
        }
      )

      setItemId('')
      setCantidad('')
      setPrecio('')
      setProveedor('')
      setUnidadCompra('kg')

      setMessage({
        error: false,
        text:
          `${isSale ? 'Venta' : 'Compra'} #${result?.id ?? 'nueva'} ` +
          'registrada correctamente.',
      })

      try {
        await refresh()
      } catch {
        setMessage({
          error: false,
          text:
            'Operación registrada, pero no se pudo actualizar ' +
            'la pantalla. Consulta el historial antes de repetir.',
        })
      }
    } catch (error) {
      setMessage({
        error: true,
        text:
          `${error.message || 'Error de la operación'}. ` +
          'Si hubo un error de red, revisa el historial ' +
          'antes de intentarlo nuevamente.',
      })
    } finally {
      busyRef.current = false
      setBusy(false)
    }
  }

  return (
    <section className="panel com-panel">
      <div className="panel-heading">
        <div>
          <h2>{isSale ? 'Registrar venta' : 'Registrar compra'}</h2>
          <p>
            {isSale
              ? 'Venta de pulpa en empaques de 230 gramos'
              : 'Compra de fruta fresca por peso'}
          </p>
        </div>
        <span className="com-tag">
          {allowed ? 'Edición habilitada' : 'Solo lectura'}
        </span>
      </div>

      {!allowed ? (
        <div className="com-explanation">
          Tu rol no tiene permiso para registrar esta operación.
        </div>
      ) : (
        <form className="com-form" onSubmit={submit}>
          <label>
            {isSale ? 'Pulpa empacada' : 'Materia prima'}
            <select
              value={itemId}
              onChange={update(setItemId)}
              required
              disabled={busy}
            >
              <option value="">Selecciona un producto...</option>

              {choices.map(item => (
                <option key={item.id} value={item.id}>
                  {item.nombre} — stock: {formato(item.stock_actual)} {item.unidad_medida}
                </option>
              ))}
            </select>
          </label>

          {!isSale && (
            <label>
              Unidad de compra
              <select
                value={unidadCompra}
                onChange={update(setUnidadCompra)}
                disabled={busy}
              >
                <option value="kg">Kilogramos (kg)</option>
                <option value="lb">Libras comerciales (500 g)</option>
              </select>
            </label>
          )}

          <label>
            {isSale
              ? 'Cantidad de empaques'
              : `Cantidad (${unidadCompra})`}

            <input
              type="number"
              min={isSale ? '1' : '0.01'}
              step={isSale ? '1' : '0.01'}
              required
              value={cantidad}
              disabled={busy}
              placeholder={isSale ? 'Ej. 5' : 'Ej. 10.50'}
              onChange={update(setCantidad)}
            />
          </label>

          {isSale ? (
            <label>
              Precio por empaque (COP)
              <input
                type="text"
                value={money(PRECIO_PULPA)}
                readOnly
              />
            </label>
          ) : (
            <label>
              Precio por kilogramo (COP/kg)
              <input
                type="number"
                min="0"
                step="0.01"
                required
                value={precio}
                disabled={busy}
                placeholder="Ej. 5000"
                onChange={update(setPrecio)}
              />
            </label>
          )}

          {!isSale && (
            <label>
              Proveedor
              <input
                type="text"
                maxLength={150}
                required
                value={proveedor}
                disabled={busy}
                placeholder="Nombre del proveedor"
                onChange={update(setProveedor)}
              />
            </label>
          )}

          <div className="com-summary">
            <div>
              <span>Stock actual</span>
              <strong>
                {selected
                  ? `${formato(stockActual)} ${selected.unidad_medida}`
                  : 'Selecciona un producto'}
              </strong>
            </div>

            {!isSale && cantidadValida && (
              <div>
                <span>Equivalencia en kg</span>
                <strong>{formato(cantidadKg)} kg</strong>
              </div>
            )}

            <div>
              <span>Total calculado</span>
              <strong>
                {cantidadValida && precioValido
                  ? money(total)
                  : '—'}
              </strong>
            </div>

            {selected && cantidadValida && (
              <div>
                <span>Stock posterior estimado</span>
                <strong>
                  {formato(stockPosterior)} {selected.unidad_medida}
                </strong>
              </div>
            )}
          </div>

          <div className="com-actions">
            <span>
              La operación se guardará en PostgreSQL.
              Confirma una sola vez.
            </span>

            <button
              type="submit"
              className="primary"
              disabled={
                busy ||
                !choices.length ||
                !selected ||
                !cantidadValida ||
                !precioValido ||
                (isSale && cantidadStock > stockActual)
              }
            >
              {busy
                ? 'Registrando...'
                : isSale
                  ? 'Registrar venta'
                  : 'Registrar compra'}
            </button>
          </div>
        </form>
      )}

      {!choices.length && (
        <p className="com-explanation">
          No hay productos disponibles para esta operación.
        </p>
      )}

      {message && (
        <div
          role="status"
          className={`notice ${
            message.error ? 'error' : 'inv-success'
          } com-message`}
        >
          {message.text}
        </div>
      )}
    </section>
  )
}
