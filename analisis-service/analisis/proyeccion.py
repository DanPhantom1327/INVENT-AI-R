"""
Proyeccion de demanda y consumo (RF09).

Modulo puro: usa numpy y scikit-learn, NO usa Django ni la base de datos.
Los datos los trae repositorio.py y la orquestacion vive en services.py.

Relacion datos -> decision:

  serie diaria de consumo (ventas o salidas de produccion)
    -> dias sin registro se rellenan con 0
    -> 3 modelos candidatos
    -> backtesting: se esconden los ultimos dias, se les pide predecir y se
       mide el error contra lo que realmente paso
    -> se usa el modelo de menor error
    -> proyeccion diaria de los proximos N dias
    -> compra sugerida de materia prima y cobertura proyectada del stock
"""
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

import numpy as np
from sklearn.linear_model import LinearRegression

# 8 semanas: alcanza para entrenar y para evaluar con 4 pruebas de 7 dias.
MIN_DIAS_HISTORIAL = 56
HORIZONTE_BACKTEST = 7
PRUEBAS_BACKTEST = 4


class DatosInsuficientes(Exception):
    """El historial es demasiado corto para evaluar y proyectar con confianza."""


# --------------------------------------------------------------------------
# 1. Procesamiento: de registros sueltos a una serie diaria continua
# --------------------------------------------------------------------------
def construir_serie(registros, fin, max_dias=365):
    """registros: iterable de (fecha, cantidad). Devuelve (inicio, y) con un
    valor por dia desde la primera fecha con datos hasta `fin` (inclusive).
    Los dias sin registro valen 0 (no hubo consumo ese dia)."""
    por_dia = {}
    for fecha, cantidad in registros:
        if fecha <= fin:
            por_dia[fecha] = por_dia.get(fecha, 0.0) + float(cantidad)
    if not por_dia:
        return None, np.array([])
    inicio = max(min(por_dia), fin - timedelta(days=max_dias - 1))
    y = np.zeros((fin - inicio).days + 1)
    for fecha, cantidad in por_dia.items():
        if fecha >= inicio:
            y[(fecha - inicio).days] = cantidad
    return inicio, y


# --------------------------------------------------------------------------
# 2. Modelos candidatos
# --------------------------------------------------------------------------
def _matriz(inicio, fechas):
    """Variables explicativas: tendencia (t) y dia de la semana (lunes = base)."""
    t = np.array([(f - inicio).days for f in fechas], dtype=float).reshape(-1, 1)
    semana = np.zeros((len(fechas), 6))
    for i, f in enumerate(fechas):
        if f.weekday() > 0:
            semana[i, f.weekday() - 1] = 1.0
    return np.hstack([t, semana])


def predecir_promedio_estacional(y, inicio, objetivo, semanas=4):
    """Modelo de referencia: promedio del mismo dia de la semana en las
    ultimas `semanas` semanas. No modela tendencia."""
    fechas = [inicio + timedelta(days=i) for i in range(len(y))]
    salida = []
    for f in objetivo:
        valores = [y[i] for i in range(len(y) - 1, -1, -1)
                   if fechas[i].weekday() == f.weekday()][:semanas]
        salida.append(float(np.mean(valores)) if valores else 0.0)
    return np.array(salida)


def predecir_regresion(y, inicio, objetivo, logaritmico=False):
    """Regresion lineal con tendencia + dia de la semana.

    logaritmico=False -> la estacionalidad suma una cantidad fija de kg.
    logaritmico=True  -> la estacionalidad multiplica el nivel (el viernes
                         vende, por ejemplo, 30 % mas que un dia normal, sin
                         importar si el negocio crece). Usa log1p y corrige el
                         sesgo de la retransformacion (smearing de Duan)."""
    fechas = [inicio + timedelta(days=i) for i in range(len(y))]
    X = _matriz(inicio, fechas)
    X_obj = _matriz(inicio, objetivo)
    if not logaritmico:
        modelo = LinearRegression().fit(X, y)
        return np.clip(modelo.predict(X_obj), 0, None)
    y_log = np.log1p(y)
    modelo = LinearRegression().fit(X, y_log)
    residuos = y_log - modelo.predict(X)
    suavizado = float(np.mean(np.exp(residuos)))
    pred = suavizado * np.exp(modelo.predict(X_obj)) - 1.0
    return np.clip(pred, 0, None)


# El orden importa: ante un empate de error gana el modelo mas simple (primero).
MODELOS = {
    "promedio_estacional_4s":
        lambda y, ini, obj: predecir_promedio_estacional(y, ini, obj, 4),
    "regresion_tendencia_semanal":
        lambda y, ini, obj: predecir_regresion(y, ini, obj, logaritmico=False),
    "regresion_log_tendencia_semanal":
        lambda y, ini, obj: predecir_regresion(y, ini, obj, logaritmico=True),
}


# --------------------------------------------------------------------------
# 3. Backtesting y seleccion
# --------------------------------------------------------------------------
def backtest(y, inicio, predictor, pruebas=PRUEBAS_BACKTEST,
             horizonte=HORIZONTE_BACKTEST):
    """Evalua un modelo con ventanas deslizantes: entrena con todo lo anterior
    al corte, predice los `horizonte` dias siguientes y compara con lo real.
    Devuelve (MAE en unidades del item, error relativo ponderado en %)."""
    n = len(y)
    errores, total_real = [], 0.0
    for k in range(pruebas, 0, -1):
        corte = n - k * horizonte
        objetivo = [inicio + timedelta(days=corte + j) for j in range(horizonte)]
        pred = predictor(y[:corte], inicio, objetivo)
        real = y[corte:corte + horizonte]
        errores.extend(np.abs(real - pred))
        total_real += float(real.sum())
    mae = float(np.mean(errores))
    wape = (float(np.sum(errores)) / total_real * 100.0) if total_real > 0 else None
    return mae, wape


def proyectar(y, inicio, objetivo):
    """Evalua los modelos, elige el de menor MAE y proyecta las fechas objetivo."""
    if len(y) < MIN_DIAS_HISTORIAL:
        raise DatosInsuficientes(
            "Se necesitan al menos %d dias de historial y hay %d."
            % (MIN_DIAS_HISTORIAL, len(y)))
    evaluados = []
    for nombre, predictor in MODELOS.items():
        mae, wape = backtest(y, inicio, predictor)
        evaluados.append({"modelo": nombre, "mae": mae, "error_relativo_pct": wape})
    mejor = min(evaluados, key=lambda e: e["mae"])
    prediccion = MODELOS[mejor["modelo"]](y, inicio, objetivo)
    return {
        "modelo": mejor["modelo"],
        "mae": mejor["mae"],
        "error_relativo_pct": mejor["error_relativo_pct"],
        "evaluados": evaluados,
        "prediccion": prediccion,
    }


# --------------------------------------------------------------------------
# 4. De la prediccion a la decision
# --------------------------------------------------------------------------
def _dec(valor, patron):
    return Decimal(str(float(valor))).quantize(Decimal(patron), rounding=ROUND_HALF_UP)


def cobertura_con_proyeccion(stock, proyeccion_diaria):
    """Dias que alcanza el stock contra el consumo PROYECTADO (no el pasado).
    Devuelve None si el stock cubre todo el horizonte proyectado."""
    restante = float(stock)
    for dia, consumo in enumerate(proyeccion_diaria):
        consumo = float(consumo)
        if consumo > 0 and restante < consumo:
            return _dec(dia + restante / consumo, "0.1")
        restante -= consumo
    return None


def compra_sugerida(stock, proyeccion_total, horizonte_dias, umbral_dias):
    """Cantidad a comprar para cubrir todo el horizonte y ademas conservar un
    colchon de `umbral_dias` dias de consumo. Nunca negativa.

    Recibe el TOTAL proyectado (no la serie diaria) para poder recalcularla
    despues desde lo que quedo guardado en la tabla proyecciones."""
    promedio = float(proyeccion_total) / horizonte_dias if horizonte_dias else 0.0
    colchon = float(umbral_dias or 0) * promedio
    return _dec(max(0.0, float(proyeccion_total) + colchon - float(stock)), "0.01")
