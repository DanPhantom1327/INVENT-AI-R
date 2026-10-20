import unittest
from decimal import Decimal as D

from analisis import calculos


class ConsumoDiarioTests(unittest.TestCase):
    def test_promedio_simple(self):
        self.assertEqual(calculos.consumo_diario_promedio(D("280"), 28), D("10"))

    def test_sin_consumo(self):
        self.assertEqual(calculos.consumo_diario_promedio(0, 28), D("0"))

    def test_ventana_invalida(self):
        with self.assertRaises(ValueError):
            calculos.consumo_diario_promedio(100, 0)


class CoberturaTests(unittest.TestCase):
    def test_cobertura_normal(self):
        # 66.14 kg de stock, 33.07 kg/dia -> 2.0 dias
        self.assertEqual(calculos.calcular_cobertura_dias(D("66.14"), D("33.07")), D("2.0"))

    def test_redondeo_a_un_decimal(self):
        self.assertEqual(calculos.calcular_cobertura_dias(D("100"), D("30")), D("3.3"))

    def test_sin_rotacion_devuelve_none(self):
        self.assertIsNone(calculos.calcular_cobertura_dias(D("50"), D("0")))

    def test_stock_cero(self):
        self.assertEqual(calculos.calcular_cobertura_dias(D("0"), D("10")), D("0.0"))

    def test_tope_maximo(self):
        self.assertEqual(
            calculos.calcular_cobertura_dias(D("999999999"), D("0.01")),
            calculos.COBERTURA_MAXIMA,
        )

    def test_acepta_floats_y_enteros(self):
        self.assertEqual(calculos.calcular_cobertura_dias(50, 10), D("5.0"))


class SeveridadTests(unittest.TestCase):
    def test_alto_por_debajo_de_la_mitad_del_umbral(self):
        self.assertEqual(calculos.clasificar_severidad(D("2.0"), 7), "ALTO")

    def test_limite_exacto_de_la_mitad_ya_es_medio(self):
        self.assertEqual(calculos.clasificar_severidad(D("3.5"), 7), "MEDIO")

    def test_medio_por_debajo_del_umbral(self):
        self.assertEqual(calculos.clasificar_severidad(D("4.4"), 5), "MEDIO")

    def test_limite_exacto_del_umbral_ya_es_bajo(self):
        self.assertEqual(calculos.clasificar_severidad(D("5.0"), 5), "BAJO")

    def test_bajo_es_aviso_preventivo(self):
        self.assertEqual(calculos.clasificar_severidad(D("6.0"), 5), "BAJO")

    def test_limite_preventivo_ya_no_alerta(self):
        self.assertIsNone(calculos.clasificar_severidad(D("6.25"), 5))

    def test_sin_riesgo(self):
        self.assertIsNone(calculos.clasificar_severidad(D("10.8"), 5))

    def test_sin_umbral_no_hay_alerta(self):
        self.assertIsNone(calculos.clasificar_severidad(D("1.0"), None))

    def test_sin_cobertura_no_hay_alerta(self):
        self.assertIsNone(calculos.clasificar_severidad(None, 5))


class CicloDeVidaAlertaTests(unittest.TestCase):
    def test_crear(self):
        self.assertEqual(calculos.decidir_accion_alerta("ALTO", False), "crear")

    def test_actualizar(self):
        self.assertEqual(calculos.decidir_accion_alerta("MEDIO", True), "actualizar")

    def test_resolver(self):
        self.assertEqual(calculos.decidir_accion_alerta(None, True), "resolver")

    def test_nada(self):
        self.assertEqual(calculos.decidir_accion_alerta(None, False), "nada")


class MensajeTests(unittest.TestCase):
    def test_incluye_los_datos_clave(self):
        msg = calculos.construir_mensaje(
            "Mango fresco", "kg", D("124.42"), D("28.3333"), D("4.4"), 5)
        self.assertIn("Mango fresco", msg)
        self.assertIn("4.4 dias", msg)
        self.assertIn("umbral configurado: 5", msg)
        self.assertIn("124.42 kg", msg)
        self.assertIn("28.33 kg", msg)
        self.assertIn("28 dias", msg)


if __name__ == "__main__":
    unittest.main()
