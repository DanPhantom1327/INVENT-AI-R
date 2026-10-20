"""
Generador de historial SINTETICO para INVENT-AI-R.

Simula N dias de operacion de una fabrica de pulpas (produccion, consumo de
fruta, compras, ventas, mermas y devoluciones) e inserta los registros
directamente en PostgreSQL con fechas pasadas, para que analisis-service
tenga una serie de tiempo sobre la cual proyectar.

IMPORTANTE (honestidad academica): estos datos son SIMULADOS. Los patrones
(estacionalidad semanal, tendencia, picos promocionales, ruido) los define
este script. Hay que declararlo asi en la documentacion del proyecto.

Los triggers de la Fase 3 se disparan en cada INSERT, igual que en operacion
real, asi que stock_actual queda consistente con el historial generado.

Uso:
    python seed_historial.py --dry-run          # simula sin tocar la BD
    python seed_historial.py --reset            # borra transacciones y genera 120 dias
    python seed_historial.py --reset --dias 180 # 180 dias
"""
import argparse
import math
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

BOGOTA = timezone(timedelta(hours=-5))  # Colombia no usa horario de verano
D = Decimal

# Factor de demanda por dia de la semana (0 = lunes). Viernes/sabado pican.
SEMANA = [0.90, 0.95, 1.00, 1.05, 1.30, 1.20, 0.55]

# base = kg de pulpa vendidos por dia en promedio; tendencia = crecimiento
# diario relativo; factor = kg de fruta por kg de pulpa.
PRODUCTOS = [
    {"pt": "Pulpa de Mora 1kg", "mp": "Mora fresca", "base": 22.0,
     "tendencia": 0.0040, "factor": 1.25, "precio_pt": 8000, "precio_mp": 3000},
    {"pt": "Pulpa de Fresa 1kg", "mp": "Fresa fresca", "base": 15.0,
     "tendencia": -0.0020, "factor": 1.20, "precio_pt": 9000, "precio_mp": 3800},
    {"pt": "Pulpa de Mango 1kg", "mp": "Mango fresco", "base": 10.0,
     "tendencia": 0.0080, "factor": 1.45, "precio_pt": 7500, "precio_mp": 2200},
]
PROVEEDORES = ["Finca La Esperanza", "Agro Santander", "Frutas del Valle"]


def q2(x):
    return D(str(x)).quantize(D("0.01"), rounding=ROUND_HALF_UP)


def a_50(x):
    return D(int(round(float(x) / 50.0) * 50))


def simular(dias, semilla):
    """Devuelve (eventos, stock_pt, stock_mp). Los eventos van en orden de
    insercion valido: compras antes de consumo, produccion antes de ventas."""
    rnd = random.Random(semilla)
    hoy = datetime.now(BOGOTA).replace(hour=0, minute=0, second=0, microsecond=0)
    inicio = hoy - timedelta(days=dias)
    stock_pt = {p["pt"]: D("0") for p in PRODUCTOS}
    stock_mp = {p["mp"]: D("0") for p in PRODUCTOS}
    eventos = []

    for t in range(dias):
        dia = inicio + timedelta(days=t)
        for p in PRODUCTOS:
            pt, mp = p["pt"], p["mp"]
            base_t = p["base"] * (1 + p["tendencia"] * t)
            ruido = max(0.3, rnd.gauss(1.0, 0.12))
            pico = 1.6 if rnd.random() < 0.04 else 1.0
            demanda = q2(base_t * SEMANA[dia.weekday()] * ruido * pico)

            # --- produccion: reponer hasta ~2 dias de demanda tras vender ---
            objetivo = q2(base_t * 2.0)
            producir = demanda + objetivo - stock_pt[pt]
            producir = max(D("0"), q2(float(producir) * rnd.uniform(0.9, 1.1)))
            if stock_pt[pt] + producir < demanda:
                producir = demanda - stock_pt[pt]
            consumo = q2(producir * D(str(p["factor"])))

            # --- compra de fruta si el stock no alcanza el punto de reorden ---
            reorden = q2(base_t * p["factor"] * 3)
            if stock_mp[mp] - consumo < reorden:
                lote = q2(base_t * p["factor"] * rnd.uniform(6, 9)) + consumo
                lote = D(int(math.ceil(float(lote) / 10.0) * 10))
                precio = a_50(p["precio_mp"] * rnd.uniform(0.90, 1.15))
                eventos.append({
                    "tipo": "compra", "ts": dia.replace(hour=5), "item": mp,
                    "cantidad": lote, "precio": precio,
                    "proveedor": rnd.choice(PROVEEDORES)})
                stock_mp[mp] += lote

            # --- produccion (ENTRADA de pulpa) y consumo (SALIDA de fruta) ---
            if producir > 0:
                eventos.append({
                    "tipo": "mov", "ts": dia.replace(hour=6), "item": pt,
                    "mov": "ENTRADA", "efecto": "SUMA", "cantidad": producir,
                    "motivo": None,
                    "ref": "SIMULADO produccion %s" % dia.strftime("%Y%m%d")})
                stock_pt[pt] += producir
                eventos.append({
                    "tipo": "mov", "ts": dia.replace(hour=6, minute=30), "item": mp,
                    "mov": "SALIDA", "efecto": "RESTA", "cantidad": consumo,
                    "motivo": None,
                    "ref": "SIMULADO consumo %s" % dia.strftime("%Y%m%d")})
                stock_mp[mp] -= consumo

            # --- merma ocasional de fruta ---
            if rnd.random() < 0.06:
                merma = q2(rnd.uniform(1, 4))
                if stock_mp[mp] >= merma:
                    eventos.append({
                        "tipo": "mov", "ts": dia.replace(hour=7), "item": mp,
                        "mov": "AJUSTE", "efecto": "RESTA", "cantidad": merma,
                        "motivo": "MERMA", "ref": "SIMULADO merma"})
                    stock_mp[mp] -= merma

            # --- ventas del dia: 2 a 4 ventas que suman la demanda ---
            n = rnd.randint(2, 4)
            pesos = [rnd.uniform(0.5, 1.5) for _ in range(n)]
            suma = sum(pesos)
            cantidades = [q2(float(demanda) * w / suma) for w in pesos[:-1]]
            ultima = demanda - sum(cantidades)
            if ultima <= 0:
                cantidades, n = [demanda], 1
            else:
                cantidades.append(ultima)
            horas = sorted(rnd.sample(range(8, 18), n))
            for cant, h in zip(cantidades, horas):
                eventos.append({
                    "tipo": "venta", "ts": dia.replace(hour=h, minute=rnd.randint(0, 59)),
                    "item": pt, "cantidad": cant,
                    "precio": a_50(p["precio_pt"] * rnd.uniform(0.97, 1.03))})
                stock_pt[pt] -= cant

            # --- devolucion ocasional de clientes ---
            if rnd.random() < 0.03:
                dev = q2(rnd.uniform(1, 3))
                eventos.append({
                    "tipo": "mov", "ts": dia.replace(hour=19), "item": pt,
                    "mov": "AJUSTE", "efecto": "SUMA", "cantidad": dev,
                    "motivo": "DEVOLUCION", "ref": "SIMULADO devolucion"})
                stock_pt[pt] += dev

    return eventos, stock_pt, stock_mp


def resumen(eventos, stock_pt, stock_mp, dias):
    ventas = [e for e in eventos if e["tipo"] == "venta"]
    compras = [e for e in eventos if e["tipo"] == "compra"]
    movs = [e for e in eventos if e["tipo"] == "mov"]
    print("Dias simulados: %d" % dias)
    print("Ventas: %d | Compras: %d | Movimientos: %d" % (len(ventas), len(compras), len(movs)))
    for p in PRODUCTOS:
        vendido = sum(e["cantidad"] for e in ventas if e["item"] == p["pt"])
        comprado = sum(e["cantidad"] for e in compras if e["item"] == p["mp"])
        print("  %-20s vendido %9s kg | stock final %8s kg" % (p["pt"], vendido, stock_pt[p["pt"]]))
        print("  %-20s comprado %8s kg | stock final %8s kg" % (p["mp"], comprado, stock_mp[p["mp"]]))


def conectar():
    try:
        import psycopg2
    except ImportError:
        sys.exit("Falta psycopg2. Activa el venv de inventario-service y reintenta.")
    return psycopg2.connect(
        dbname=os.environ.get("PGDATABASE", "invent_air_db"),
        user=os.environ.get("PGUSER", "grability"),
        password=os.environ.get("PGPASSWORD", ""),
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"))


def verificar_zona_horaria(cur):
    cur.execute("""SELECT data_type FROM information_schema.columns
                   WHERE table_schema='ventas_schema' AND table_name='ventas'
                   AND column_name='fecha'""")
    tipo = cur.fetchone()[0]
    if tipo != "timestamp with time zone":
        sys.exit("Las columnas de fecha aun son '%s'. Corre primero "
                 "fix_timestamptz.sql (ver instrucciones) y reintenta." % tipo)


def obtener_o_crear_item(cur, tipo, nombre, umbral):
    cur.execute("SELECT id FROM inventario_schema.items_inventario "
                "WHERE tipo=%s AND nombre=%s", (tipo, nombre))
    fila = cur.fetchone()
    if fila:
        return fila[0]
    cur.execute("INSERT INTO inventario_schema.items_inventario "
                "(tipo, nombre, unidad_medida, umbral_dias_cobertura) "
                "VALUES (%s, %s, 'kg', %s) RETURNING id", (tipo, nombre, umbral))
    return cur.fetchone()[0]


def insertar(cur, eventos, ids, usuario_id):
    for e in eventos:
        item_id = ids[e["item"]]
        if e["tipo"] == "venta":
            cur.execute(
                "INSERT INTO ventas_schema.ventas (producto_id, cantidad, "
                "precio_unitario, total, vendedor_id, fecha) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (item_id, e["cantidad"], e["precio"],
                 e["cantidad"] * e["precio"], usuario_id, e["ts"]))
        elif e["tipo"] == "compra":
            cur.execute(
                "INSERT INTO compras_schema.compras (materia_prima_id, cantidad, "
                "precio_unitario, total, proveedor, analista_id, fecha) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (item_id, e["cantidad"], e["precio"],
                 e["cantidad"] * e["precio"], e["proveedor"], usuario_id, e["ts"]))
        else:
            cur.execute(
                "INSERT INTO inventario_schema.movimientos_inventario (item_id, "
                "tipo_movimiento, efecto, cantidad, motivo_ajuste, usuario_id, "
                "referencia, fecha) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (item_id, e["mov"], e["efecto"], e["cantidad"], e["motivo"],
                 usuario_id, e["ref"], e["ts"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dias", type=int, default=120)
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--usuario-id", type=int, default=1)
    ap.add_argument("--reset", action="store_true",
                    help="BORRA ventas, compras y movimientos existentes y pone stock en 0")
    ap.add_argument("--dry-run", action="store_true",
                    help="simula y muestra el resumen sin tocar la base de datos")
    args = ap.parse_args()

    eventos, stock_pt, stock_mp = simular(args.dias, args.semilla)
    resumen(eventos, stock_pt, stock_mp, args.dias)
    if args.dry_run:
        print("\n(dry-run: no se escribio nada en la base de datos)")
        return

    conn = conectar()
    try:
        cur = conn.cursor()
        verificar_zona_horaria(cur)

        cur.execute("""SELECT (SELECT count(*) FROM ventas_schema.ventas)
                            + (SELECT count(*) FROM compras_schema.compras)
                            + (SELECT count(*) FROM inventario_schema.movimientos_inventario)""")
        existentes = cur.fetchone()[0]
        if existentes and not args.reset:
            sys.exit("Ya hay %d transacciones en la BD. Usa --reset si quieres "
                     "BORRARLAS y generar el historial desde cero." % existentes)
        if args.reset:
            cur.execute("TRUNCATE ventas_schema.ventas, compras_schema.compras, "
                        "inventario_schema.movimientos_inventario RESTART IDENTITY")
            cur.execute("UPDATE inventario_schema.items_inventario SET stock_actual = 0")
            print("\nTransacciones anteriores borradas, stock en 0.")

        ids = {}
        for p in PRODUCTOS:
            ids[p["pt"]] = obtener_o_crear_item(cur, "PRODUCTO_TERMINADO", p["pt"], 7)
            ids[p["mp"]] = obtener_o_crear_item(cur, "MATERIA_PRIMA", p["mp"], 5)

        insertar(cur, eventos, ids, args.usuario_id)
        conn.commit()

        print("\nInsertado. Stock en BD vs simulacion (deben coincidir):")
        for nombre, esperado in list(stock_pt.items()) + list(stock_mp.items()):
            cur.execute("SELECT stock_actual FROM inventario_schema.items_inventario "
                        "WHERE id=%s", (ids[nombre],))
            real = cur.fetchone()[0]
            marca = "OK" if real == esperado else "DIFIERE"
            print("  %-20s BD %9s | simulado %9s  %s" % (nombre, real, esperado, marca))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
