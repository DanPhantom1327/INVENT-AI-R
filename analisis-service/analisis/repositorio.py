"""
Lecturas SQL sobre los datos de OTROS servicios (inventario, ventas).
Este servicio solo LEE esos esquemas; nunca escribe en ellos.
Las consultas usan nombres con esquema explicito porque el search_path de
esta conexion apunta a analisis_schema.
"""
from django.db import connection


def _filas_como_dict(cursor):
    columnas = [c[0] for c in cursor.description]
    return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]


def items_activos():
    sql = """
        SELECT id, tipo, nombre, unidad_medida, stock_actual, umbral_dias_cobertura
          FROM inventario_schema.items_inventario
         WHERE activo = TRUE
         ORDER BY id
    """
    with connection.cursor() as cur:
        cur.execute(sql)
        return _filas_como_dict(cur)


def consumo_total(item, dias):
    """Total consumido en los ultimos `dias` dias.

    Producto terminado -> lo VENDIDO (ventas_schema.ventas).
    Materia prima      -> lo GASTADO en produccion (movimientos SALIDA).
    """
    if item["tipo"] == "PRODUCTO_TERMINADO":
        sql = """
            SELECT COALESCE(SUM(cantidad), 0)
              FROM ventas_schema.ventas
             WHERE producto_id = %s
               AND fecha >= now() - make_interval(days => %s)
        """
    else:
        sql = """
            SELECT COALESCE(SUM(cantidad), 0)
              FROM inventario_schema.movimientos_inventario
             WHERE item_id = %s
               AND tipo_movimiento = 'SALIDA'
               AND fecha >= now() - make_interval(days => %s)
        """
    with connection.cursor() as cur:
        cur.execute(sql, [item["id"], dias])
        return cur.fetchone()[0]


def ultima_cobertura_por_item():
    sql = """
        SELECT DISTINCT ON (c.item_id)
               c.item_id, i.nombre, i.tipo, i.unidad_medida, i.stock_actual,
               i.umbral_dias_cobertura AS umbral_dias,
               c.dias_cobertura_estimados AS cobertura_dias, c.fecha_calculo
          FROM analisis_schema.cobertura_stock c
          JOIN inventario_schema.items_inventario i ON i.id = c.item_id
         ORDER BY c.item_id, c.fecha_calculo DESC
    """
    with connection.cursor() as cur:
        cur.execute(sql)
        return _filas_como_dict(cur)


def alertas(estado=None):
    sql = """
        SELECT a.id, a.item_id, i.nombre AS item_nombre, a.tipo_alerta,
               a.nivel_severidad, a.mensaje, a.estado,
               a.fecha_generacion, a.fecha_resolucion
          FROM analisis_schema.alertas a
          JOIN inventario_schema.items_inventario i ON i.id = a.item_id
    """
    params = []
    if estado:
        sql += " WHERE a.estado = %s"
        params.append(estado)
    sql += """
         ORDER BY CASE a.nivel_severidad WHEN 'ALTO' THEN 1 WHEN 'MEDIO' THEN 2 ELSE 3 END,
                  a.fecha_generacion DESC
    """
    with connection.cursor() as cur:
        cur.execute(sql, params)
        return _filas_como_dict(cur)


ZONA_HORARIA = "America/Bogota"


def registros_diarios(item, max_dias=365):
    """Consumo agrupado por DIA LOCAL (Bogota): lista de (fecha, total).
    Producto terminado -> ventas; materia prima -> salidas de produccion."""
    if item["tipo"] == "PRODUCTO_TERMINADO":
        sql = """
            SELECT (fecha AT TIME ZONE %s)::date AS dia, SUM(cantidad)
              FROM ventas_schema.ventas
             WHERE producto_id = %s
               AND fecha >= now() - make_interval(days => %s)
             GROUP BY 1
             ORDER BY 1
        """
    else:
        sql = """
            SELECT (fecha AT TIME ZONE %s)::date AS dia, SUM(cantidad)
              FROM inventario_schema.movimientos_inventario
             WHERE item_id = %s
               AND tipo_movimiento = 'SALIDA'
               AND fecha >= now() - make_interval(days => %s)
             GROUP BY 1
             ORDER BY 1
        """
    with connection.cursor() as cur:
        cur.execute(sql, [ZONA_HORARIA, item["id"], max_dias])
        return [(fila[0], fila[1]) for fila in cur.fetchall()]


def ultimas_proyecciones_por_item():
    sql = """
        SELECT DISTINCT ON (p.item_id)
               p.item_id, i.nombre, i.tipo, i.unidad_medida, i.stock_actual,
               i.umbral_dias_cobertura AS umbral_dias,
               p.tipo_proyeccion, p.valor_proyectado AS proyeccion_total,
               p.horizonte_dias, p.modelo_usado, p.fecha_generacion
          FROM analisis_schema.proyecciones p
          JOIN inventario_schema.items_inventario i ON i.id = p.item_id
         ORDER BY p.item_id, p.fecha_generacion DESC
    """
    with connection.cursor() as cur:
        cur.execute(sql)
        return _filas_como_dict(cur)
