import unittest
from datetime import date, timedelta
from decimal import Decimal as D

import numpy as np

from analisis import proyeccion as p

INICIO = date(2026, 1, 5)  # lunes
SEMANA_ADITIVA = [0, 1, 2, 3, 8, 6, -5]


def serie_aditiva(n, base=20.0, pendiente=0.2):
    """Serie sin ruido: nivel + tendencia lineal + efecto fijo por dia de semana."""
    return np.array([base + pendiente * t + SEMANA_ADITIVA[(INICIO + timedelta(days=t)).weekday()]
                     for t in range(n)])


def fechas(inicio, n):
    return [inicio + timedelta(days=i) for i in range(n)]


class ConstruirSerieTests(unittest.TestCase):
    def test_rellena_con_cero_los_dias_sin_registro(self):
        regs = [(date(2026, 3, 1), 10), (date(2026, 3, 4), 5)]
        inicio, y = p.construir_serie(regs, date(2026, 3, 5))
        self.assertEqual(inicio, date(2026, 3, 1))
        self.assertEqual(y.tolist(), [10, 0, 0, 5, 0])

    def test_suma_varios_registros_del_mismo_dia(self):
        regs = [(date(2026, 3, 1), 4), (date(2026, 3, 1), 6.5)]
        _, y = p.construir_serie(regs, date(2026, 3, 1))
        self.assertEqual(y.tolist(), [10.5])

    def test_ignora_registros_posteriores_a_fin(self):
        regs = [(date(2026, 3, 1), 4), (date(2026, 3, 9), 99)]
        _, y = p.construir_serie(regs, date(2026, 3, 3))
        self.assertEqual(y.tolist(), [4, 0, 0])

    def test_sin_datos(self):
        inicio, y = p.construir_serie([], date(2026, 3, 3))
        self.assertIsNone(inicio)
        self.assertEqual(len(y), 0)

    def test_respeta_max_dias(self):
        regs = [(date(2026, 1, 1), 1), (date(2026, 3, 1), 2)]
        inicio, y = p.construir_serie(regs, date(2026, 3, 1), max_dias=10)
        self.assertEqual(len(y), 10)
        self.assertEqual(inicio, date(2026, 2, 20))
        self.assertEqual(y[-1], 2)

    def test_acepta_decimal(self):
        _, y = p.construir_serie([(date(2026, 3, 1), D("12.34"))], date(2026, 3, 1))
        self.assertAlmostEqual(y[0], 12.34)


class ModelosTests(unittest.TestCase):
    def test_promedio_estacional_exacto_en_serie_periodica(self):
        y = np.array([SEMANA_ADITIVA[(INICIO + timedelta(days=t)).weekday()] + 10.0
                      for t in range(70)])
        obj = fechas(INICIO + timedelta(days=70), 14)
        pred = p.predecir_promedio_estacional(y, INICIO, obj)
        esperado = [10.0 + SEMANA_ADITIVA[f.weekday()] for f in obj]
        np.testing.assert_allclose(pred, esperado, atol=1e-9)

    def test_regresion_aditiva_recupera_tendencia_y_estacionalidad(self):
        n = 90
        y = serie_aditiva(n)
        obj = fechas(INICIO + timedelta(days=n), 14)
        esperado = [20.0 + 0.2 * (n + i) + SEMANA_ADITIVA[f.weekday()] for i, f in enumerate(obj)]
        pred = p.predecir_regresion(y, INICIO, obj, logaritmico=False)
        np.testing.assert_allclose(pred, esperado, atol=1e-6)

    def test_nunca_predice_negativos(self):
        y = np.maximum(serie_aditiva(60, base=2.0, pendiente=-0.1), 0)
        obj = fechas(INICIO + timedelta(days=60), 30)
        for logaritmico in (False, True):
            pred = p.predecir_regresion(y, INICIO, obj, logaritmico=logaritmico)
            self.assertTrue((pred >= 0).all())

    def test_serie_constante(self):
        y = np.full(60, 12.0)
        obj = fechas(INICIO + timedelta(days=60), 7)
        for predictor in p.MODELOS.values():
            np.testing.assert_allclose(predictor(y, INICIO, obj), 12.0, atol=1e-6)


class BacktestYSeleccionTests(unittest.TestCase):
    def test_backtest_sin_error_en_serie_periodica(self):
        y = np.array([SEMANA_ADITIVA[(INICIO + timedelta(days=t)).weekday()] + 10.0
                      for t in range(70)])
        mae, wape = p.backtest(y, INICIO, MODELOS_ESTACIONAL)
        self.assertAlmostEqual(mae, 0.0, places=9)

    def test_elige_la_regresion_cuando_hay_tendencia(self):
        y = serie_aditiva(90)
        obj = fechas(INICIO + timedelta(days=90), 14)
        r = p.proyectar(y, INICIO, obj)
        self.assertEqual(r["modelo"], "regresion_tendencia_semanal")
        self.assertLess(r["mae"], 1e-6)
        nombres = [e["modelo"] for e in r["evaluados"]]
        self.assertEqual(nombres, list(p.MODELOS))
        baseline = next(e for e in r["evaluados"] if e["modelo"] == "promedio_estacional_4s")
        self.assertGreater(baseline["mae"], r["mae"])
        self.assertEqual(len(r["prediccion"]), 14)

    def test_empate_gana_el_modelo_mas_simple(self):
        y = np.full(60, 5.0)
        r = p.proyectar(y, INICIO, fechas(INICIO + timedelta(days=60), 7))
        self.assertEqual(r["modelo"], "promedio_estacional_4s")

    def test_serie_toda_en_cero(self):
        r = p.proyectar(np.zeros(60), INICIO, fechas(INICIO + timedelta(days=60), 7))
        self.assertEqual(float(r["prediccion"].sum()), 0.0)
        self.assertIsNone(r["error_relativo_pct"])

    def test_historial_corto_lanza_excepcion(self):
        with self.assertRaises(p.DatosInsuficientes):
            p.proyectar(np.ones(p.MIN_DIAS_HISTORIAL - 1), INICIO,
                        fechas(INICIO, 7))

    def test_justo_en_el_minimo_funciona(self):
        r = p.proyectar(serie_aditiva(p.MIN_DIAS_HISTORIAL), INICIO,
                        fechas(INICIO + timedelta(days=p.MIN_DIAS_HISTORIAL), 7))
        self.assertEqual(len(r["prediccion"]), 7)


def MODELOS_ESTACIONAL(y, ini, obj):
    return p.predecir_promedio_estacional(y, ini, obj, 4)


class DecisionTests(unittest.TestCase):
    def test_cobertura_exacta(self):
        self.assertEqual(p.cobertura_con_proyeccion(50, [10] * 10), D("5.0"))

    def test_cobertura_fraccionaria(self):
        self.assertEqual(p.cobertura_con_proyeccion(55, [10] * 10), D("5.5"))

    def test_stock_cubre_todo_el_horizonte(self):
        self.assertIsNone(p.cobertura_con_proyeccion(1000, [10] * 10))

    def test_sin_stock(self):
        self.assertEqual(p.cobertura_con_proyeccion(0, [10] * 5), D("0.0"))

    def test_dias_iniciales_sin_consumo(self):
        self.assertEqual(p.cobertura_con_proyeccion(5, [0, 0, 10, 10]), D("2.5"))

    def test_compra_cubre_horizonte_mas_colchon(self):
        # 14 dias x 10 = 140; colchon 5 dias x 10 = 50; stock 100 -> comprar 90
        self.assertEqual(p.compra_sugerida(100, 140, 14, 5), D("90.00"))

    def test_compra_nunca_es_negativa(self):
        self.assertEqual(p.compra_sugerida(10000, 140, 14, 5), D("0.00"))

    def test_compra_sin_umbral(self):
        self.assertEqual(p.compra_sugerida(40, 70, 7, None), D("30.00"))


if __name__ == "__main__":
    unittest.main()
