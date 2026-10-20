"""
Calculos puros de cobertura de stock y alertas tempranas (RF10, RF11).

Este modulo NO importa Django ni toca la base de datos: recibe numeros y
devuelve numeros. Por eso se prueba con `python -m unittest` sin levantar
nada. Los datos los trae repositorio.py y la orquestacion vive en
services.py (capa Presenter de MVP).

Flujo:  historial (ventas / consumo)  ->  consumo diario promedio
        ->  cobertura en dias = stock / consumo diario
        ->  comparacion contra el umbral del item  ->  severidad de la alerta
"""
from decimal import Decimal, ROUND_HALF_UP

# 28 dias = 4 semanas completas: cada dia de la semana pesa exactamente igual
# en el promedio, asi el patron semanal (viernes alto, domingo bajo) no sesga
# la estimacion del consumo diario.
VENTANA_DIAS = 28

# La columna cobertura_stock.dias_cobertura_estimados es NUMERIC(6,1).
COBERTURA_MAXIMA = Decimal("9999.9")

TIPO_ALERTA = "RIESGO_DESABASTECIMIENTO"

# Alerta ALTA  : cobertura < 50 % del umbral
# Alerta MEDIA : cobertura < umbral
# Alerta BAJA  : cobertura < 125 % del umbral (aviso preventivo)
FACTOR_ALTO = Decimal("0.5")
FACTOR_PREVENTIVO = Decimal("1.25")


def a_decimal(valor):
    return valor if isinstance(valor, Decimal) else Decimal(str(valor))


def redondear(valor, patron="0.01"):
    return a_decimal(valor).quantize(Decimal(patron), rounding=ROUND_HALF_UP)


def consumo_diario_promedio(total_consumido, dias=VENTANA_DIAS):
    """Promedio diario de lo consumido (vendido o gastado en produccion)."""
    if dias <= 0:
        raise ValueError("dias debe ser mayor que cero")
    return a_decimal(total_consumido) / Decimal(dias)


def calcular_cobertura_dias(stock_actual, consumo_diario):
    """Dias que alcanza el stock al ritmo de consumo actual.

    Devuelve None si no hay consumo (sin rotacion): no se puede estimar.
    """
    stock = a_decimal(stock_actual)
    consumo = a_decimal(consumo_diario)
    if consumo <= 0:
        return None
    dias = min(stock / consumo, COBERTURA_MAXIMA)
    return redondear(dias, "0.1")


def clasificar_severidad(cobertura_dias, umbral_dias):
    """None (sin alerta), 'BAJO', 'MEDIO' o 'ALTO'.

    Sin umbral configurado o sin cobertura calculable no hay alerta.
    """
    if cobertura_dias is None or umbral_dias is None:
        return None
    umbral = a_decimal(umbral_dias)
    cobertura = a_decimal(cobertura_dias)
    if cobertura < umbral * FACTOR_ALTO:
        return "ALTO"
    if cobertura < umbral:
        return "MEDIO"
    if cobertura < umbral * FACTOR_PREVENTIVO:
        return "BAJO"
    return None


def decidir_accion_alerta(severidad, hay_alerta_activa):
    """Ciclo de vida de la alerta para evitar duplicados.

    'crear'      : hay riesgo y no habia alerta abierta
    'actualizar' : hay riesgo y ya habia una alerta abierta (refresca severidad y texto)
    'resolver'   : ya no hay riesgo y habia una alerta abierta
    'nada'       : no hay riesgo ni alerta abierta
    """
    if severidad is not None:
        return "actualizar" if hay_alerta_activa else "crear"
    return "resolver" if hay_alerta_activa else "nada"


def construir_mensaje(nombre, unidad, stock, consumo_diario, cobertura_dias,
                      umbral_dias, ventana_dias=VENTANA_DIAS):
    return (
        "%s: cobertura estimada de %s dias (umbral configurado: %s). "
        "Stock %s %s; consumo diario promedio %s %s en los ultimos %d dias."
        % (nombre, cobertura_dias, umbral_dias,
           redondear(stock), unidad, redondear(consumo_diario), unidad,
           ventana_dias)
    )
