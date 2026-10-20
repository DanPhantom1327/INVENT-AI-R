"""
Presenter (capa MVP): orquesta repositorio (datos), calculos (reglas) y
modelos (persistencia). Las vistas solo llaman a este modulo.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from . import calculos, proyeccion, repositorio
from .models import Alerta, CoberturaStock, Proyeccion


class CoberturaService:
    @staticmethod
    @transaction.atomic
    def calcular_y_alertar(ventana_dias=calculos.VENTANA_DIAS):
        """RF10 + RF11: calcula la cobertura de cada item activo, guarda la
        foto del dia y crea / actualiza / resuelve su alerta segun el umbral."""
        resultados = []
        for item in repositorio.items_activos():
            total = repositorio.consumo_total(item, ventana_dias)
            consumo = calculos.consumo_diario_promedio(total, ventana_dias)
            cobertura = calculos.calcular_cobertura_dias(item["stock_actual"], consumo)
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
                "cobertura_dias": cobertura,
                "umbral_dias": umbral,
                "severidad": severidad,
                "accion_alerta": accion,
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
        ayer = hoy - timedelta(days=1)
        objetivo = [hoy + timedelta(days=i) for i in range(horizonte_dias)]
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
            registros = repositorio.registros_diarios(item)
            if not registros:
                resultado.update(estado="SIN_HISTORIAL",
                                 detalle="El item no tiene consumo registrado.")
                resultados.append(resultado)
                continue

            # La serie termina en el ultimo dia con datos (nunca hoy: el dia
            # en curso esta incompleto). Si hay dias sin registros recientes
            # se avisa, porque el modelo proyecta desde un historial atrasado.
            fin = min(max(fecha for fecha, _ in registros), ayer)
            inicio, y = proyeccion.construir_serie(registros, fin)
            try:
                r = proyeccion.proyectar(y, inicio, objetivo)
            except proyeccion.DatosInsuficientes as e:
                resultado.update(estado="DATOS_INSUFICIENTES", detalle=str(e))
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
                ultimo_dato=fin, dias_sin_datos_recientes=(ayer - fin).days,
                proyeccion_total=total, promedio_diario=total / horizonte_dias,
                cobertura_proyectada_dias=proyeccion.cobertura_con_proyeccion(
                    item["stock_actual"], diaria),
                compra_sugerida=(proyeccion.compra_sugerida(
                    item["stock_actual"], total, horizonte_dias,
                    item["umbral_dias_cobertura"]) if es_materia_prima else None),
                proyeccion_diaria=[{"fecha": f, "cantidad": float(v)}
                                   for f, v in zip(objetivo, diaria)],
                modelos_evaluados=r["evaluados"])
            if resultado["dias_sin_datos_recientes"] > 0:
                resultado["detalle"] = (
                    "El historial termina el %s (%d dia(s) sin registros recientes); "
                    "la proyeccion parte de datos atrasados."
                    % (fin.isoformat(), resultado["dias_sin_datos_recientes"]))
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
