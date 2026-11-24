"""
Presenter (capa MVP): orquesta repositorio (datos), calculos (reglas) y
modelos (persistencia). Las vistas solo llaman a este modulo.
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from . import calculos, proyeccion, repositorio
from .models import Alerta, CoberturaStock, Proyeccion

logger = logging.getLogger(__name__)


def _proyectar_item(item, hoy, horizonte_dias):
    """Proyecta el consumo de un item para los proximos `horizonte_dias` dias.

    Lo comparten la generacion de proyecciones y el calculo de alertas.
    Devuelve un dict con: estado ('OK' | 'SIN_HISTORIAL' | 'DATOS_INSUFICIENTES'),
    detalle (aviso en texto o None), fin (ultimo dia usado), dias_sin_datos,
    objetivo (fechas proyectadas) y r (resultado de proyeccion.proyectar o None).
    """
    ayer = hoy - timedelta(days=1)
    objetivo = [hoy + timedelta(days=i) for i in range(horizonte_dias)]
    salida = {"estado": "OK", "detalle": None, "fin": None,
              "dias_sin_datos": None, "objetivo": objetivo, "r": None}

    registros = repositorio.registros_diarios(item)
    if not registros:
        salida.update(estado="SIN_HISTORIAL",
                      detalle="El item no tiene consumo registrado.")
        return salida

    # La serie termina en el ultimo dia con datos (nunca hoy: el dia en curso
    # esta incompleto). Si hay dias sin registros recientes se avisa, porque
    # el modelo proyecta desde un historial atrasado.
    fin = min(max(fecha for fecha, _ in registros), ayer)
    inicio, y = proyeccion.construir_serie(registros, fin)
    try:
        r = proyeccion.proyectar(y, inicio, objetivo)
    except proyeccion.DatosInsuficientes as e:
        salida.update(estado="DATOS_INSUFICIENTES", detalle=str(e), fin=fin)
        return salida

    dias_sin_datos = (ayer - fin).days
    salida.update(fin=fin, dias_sin_datos=dias_sin_datos, r=r)
    if dias_sin_datos > 0:
        salida["detalle"] = (
            "El historial termina el %s (%d dia(s) sin registros recientes); "
            "la proyeccion parte de datos atrasados."
            % (fin.isoformat(), dias_sin_datos))
    return salida


class CoberturaService:
    @staticmethod
    @transaction.atomic
    def calcular_y_alertar(ventana_dias=calculos.VENTANA_DIAS):
        """RF10 + RF11. Para cada item activo:
          1. cobertura HISTORICA  = stock / consumo diario de la ventana pasada
          2. cobertura PROYECTADA = dias que alcanza el stock contra el consumo
             que el modelo espera para los proximos dias
          3. cobertura efectiva   = la menor de las dos
          4. se guarda la foto del dia y la alerta se crea, actualiza o resuelve
        """
        hoy = timezone.localdate()
        resultados = []
        for item in repositorio.items_activos():
            total = repositorio.consumo_total(item, ventana_dias)
            consumo = calculos.consumo_diario_promedio(total, ventana_dias)
            cob_historica = calculos.calcular_cobertura_dias(item["stock_actual"], consumo)

            cob_proyectada, consumo_proyectado, modelo, advertencia = None, None, None, None
            dias_consumo_proyectado = 0
            try:
                proy = _proyectar_item(item, hoy, calculos.HORIZONTE_ALERTAS)
            except Exception:  # la proyeccion nunca debe tumbar el calculo de alertas
                logger.exception("No se pudo proyectar el item %s", item["id"])
                proy = None
                advertencia = "No se pudo proyectar el consumo; la alerta usa solo el historial."
            if proy is not None:
                advertencia = proy["detalle"]
                if proy["r"] is not None:
                    diaria = proy["r"]["prediccion"]
                    modelo = proy["r"]["modelo"]
                    cob_proyectada = proyeccion.cobertura_con_proyeccion(
                        item["stock_actual"], diaria)
                    primeros = diaria[:14]
                    dias_consumo_proyectado = len(primeros)
                    consumo_proyectado = float(primeros.sum()) / dias_consumo_proyectado

            cobertura, base = calculos.cobertura_efectiva(cob_historica, cob_proyectada)
            umbral = item["umbral_dias_cobertura"]
            severidad = calculos.clasificar_severidad(cobertura, umbral)

            if cobertura is not None:
                CoberturaStock.objects.create(
                    item_id=item["id"], dias_cobertura_estimados=cobertura)

            activa = Alerta.objects.filter(
                item_id=item["id"], tipo_alerta=calculos.TIPO_ALERTA,
                estado=Alerta.ACTIVA).first()
            accion = calculos.decidir_accion_alerta(severidad, activa is not None)

            if accion in ("crear", "actualizar"):
                if base == "PROYECTADO":
                    mensaje = calculos.construir_mensaje_proyectado(
                        item["nombre"], item["unidad_medida"], item["stock_actual"],
                        consumo_proyectado, cobertura, umbral, modelo,
                        dias_consumo_proyectado)
                else:
                    mensaje = calculos.construir_mensaje(
                        item["nombre"], item["unidad_medida"], item["stock_actual"],
                        consumo, cobertura, umbral, ventana_dias)
                if accion == "crear":
                    Alerta.objects.create(
                        item_id=item["id"], tipo_alerta=calculos.TIPO_ALERTA,
                        nivel_severidad=severidad, mensaje=mensaje)
                else:
                    activa.nivel_severidad = severidad
                    activa.mensaje = mensaje
                    activa.save(update_fields=["nivel_severidad", "mensaje"])
            elif accion == "resolver":
                activa.estado = Alerta.RESUELTA
                activa.fecha_resolucion = timezone.now()
                activa.save(update_fields=["estado", "fecha_resolucion"])

            resultados.append({
                "item_id": item["id"],
                "nombre": item["nombre"],
                "tipo": item["tipo"],
                "unidad_medida": item["unidad_medida"],
                "stock_actual": item["stock_actual"],
                "consumo_diario": calculos.redondear(consumo),
                "cobertura_historica_dias": cob_historica,
                "cobertura_proyectada_dias": cob_proyectada,
                "cobertura_dias": cobertura,
                "base_alerta": base,
                "umbral_dias": umbral,
                "severidad": severidad,
                "accion_alerta": accion,
                "advertencia": advertencia,
            })
        return resultados

    @staticmethod
    def ultima_cobertura():
        filas = repositorio.ultima_cobertura_por_item()
        for fila in filas:
            fila["severidad"] = calculos.clasificar_severidad(
                fila["cobertura_dias"], fila["umbral_dias"])
        return filas


class AlertaService:
    @staticmethod
    def listar(estado=None):
        return repositorio.alertas(estado)


class ProyeccionService:
    @staticmethod
    @transaction.atomic
    def generar(horizonte_dias=14):
        """RF09: proyecta el consumo de los proximos `horizonte_dias` dias para
        cada item, eligiendo el mejor modelo por backtesting, y guarda el total
        proyectado en la tabla proyecciones."""
        hoy = timezone.localdate()
        resultados = []

        for item in repositorio.items_activos():
            resultado = {
                "item_id": item["id"], "nombre": item["nombre"], "tipo": item["tipo"],
                "unidad_medida": item["unidad_medida"], "estado": "OK", "detalle": None,
                "modelo_usado": None, "mae": None, "error_relativo_pct": None,
                "ultimo_dato": None, "dias_sin_datos_recientes": None,
                "proyeccion_total": None, "promedio_diario": None,
                "cobertura_proyectada_dias": None, "compra_sugerida": None,
                "proyeccion_diaria": [], "modelos_evaluados": [],
            }
            proy = _proyectar_item(item, hoy, horizonte_dias)
            resultado.update(estado=proy["estado"], detalle=proy["detalle"])
            r = proy["r"]
            if r is None:
                resultados.append(resultado)
                continue

            diaria = r["prediccion"]
            total = float(diaria.sum())
            es_materia_prima = item["tipo"] == "MATERIA_PRIMA"

            Proyeccion.objects.create(
                item_id=item["id"],
                tipo_proyeccion=(Proyeccion.NECESIDAD_MATERIA_PRIMA if es_materia_prima
                                 else Proyeccion.DEMANDA),
                valor_proyectado=calculos.redondear(total),
                horizonte_dias=horizonte_dias,
                modelo_usado=r["modelo"])

            resultado.update(
                modelo_usado=r["modelo"], mae=r["mae"],
                error_relativo_pct=r["error_relativo_pct"],
                ultimo_dato=proy["fin"], dias_sin_datos_recientes=proy["dias_sin_datos"],
                proyeccion_total=total, promedio_diario=total / horizonte_dias,
                cobertura_proyectada_dias=proyeccion.cobertura_con_proyeccion(
                    item["stock_actual"], diaria),
                compra_sugerida=(proyeccion.compra_sugerida(
                    item["stock_actual"], total, horizonte_dias,
                    item["umbral_dias_cobertura"]) if es_materia_prima else None),
                proyeccion_diaria=[{"fecha": f, "cantidad": float(v)}
                                   for f, v in zip(proy["objetivo"], diaria)],
                modelos_evaluados=r["evaluados"])
            resultados.append(resultado)
        return resultados

    @staticmethod
    def ultimas():
        filas = repositorio.ultimas_proyecciones_por_item()
        for fila in filas:
            total, horizonte = fila["proyeccion_total"], fila["horizonte_dias"]
            fila["promedio_diario"] = total / horizonte
            fila["compra_sugerida"] = (
                proyeccion.compra_sugerida(
                    fila["stock_actual"], total, horizonte, fila["umbral_dias"])
                if fila["tipo"] == "MATERIA_PRIMA" else None)
        return filas
