"""View (capa MVP, contrato de datos): formato de las respuestas JSON."""
from rest_framework import serializers


class CoberturaCalculadaSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    nombre = serializers.CharField()
    tipo = serializers.CharField()
    unidad_medida = serializers.CharField()
    stock_actual = serializers.DecimalField(max_digits=12, decimal_places=2)
    consumo_diario = serializers.DecimalField(max_digits=12, decimal_places=2)
    cobertura_historica_dias = serializers.DecimalField(max_digits=6, decimal_places=1, allow_null=True)
    cobertura_proyectada_dias = serializers.DecimalField(max_digits=6, decimal_places=1, allow_null=True)
    cobertura_dias = serializers.DecimalField(max_digits=6, decimal_places=1, allow_null=True)
    base_alerta = serializers.CharField(allow_null=True)
    umbral_dias = serializers.IntegerField(allow_null=True)
    severidad = serializers.CharField(allow_null=True)
    accion_alerta = serializers.CharField()
    advertencia = serializers.CharField(allow_null=True)


class CoberturaGuardadaSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    nombre = serializers.CharField()
    tipo = serializers.CharField()
    unidad_medida = serializers.CharField()
    stock_actual = serializers.DecimalField(max_digits=12, decimal_places=2)
    cobertura_dias = serializers.DecimalField(max_digits=6, decimal_places=1)
    umbral_dias = serializers.IntegerField(allow_null=True)
    severidad = serializers.CharField(allow_null=True)
    fecha_calculo = serializers.DateTimeField()


class AlertaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    item_id = serializers.IntegerField()
    item_nombre = serializers.CharField()
    tipo_alerta = serializers.CharField()
    nivel_severidad = serializers.CharField()
    mensaje = serializers.CharField()
    estado = serializers.CharField()
    fecha_generacion = serializers.DateTimeField()
    fecha_resolucion = serializers.DateTimeField(allow_null=True)


class GenerarProyeccionSerializer(serializers.Serializer):
    horizonte_dias = serializers.IntegerField(min_value=1, max_value=30, required=False, default=14)


class DiaProyectadoSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    cantidad = serializers.DecimalField(max_digits=12, decimal_places=2)


class ModeloEvaluadoSerializer(serializers.Serializer):
    modelo = serializers.CharField()
    mae = serializers.DecimalField(max_digits=12, decimal_places=2)
    error_relativo_pct = serializers.DecimalField(max_digits=6, decimal_places=1, allow_null=True)


class ProyeccionResultadoSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    nombre = serializers.CharField()
    tipo = serializers.CharField()
    unidad_medida = serializers.CharField()
    estado = serializers.CharField()
    detalle = serializers.CharField(allow_null=True)
    modelo_usado = serializers.CharField(allow_null=True)
    mae = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    error_relativo_pct = serializers.DecimalField(max_digits=6, decimal_places=1, allow_null=True)
    ultimo_dato = serializers.DateField(allow_null=True)
    dias_sin_datos_recientes = serializers.IntegerField(allow_null=True)
    proyeccion_total = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    promedio_diario = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    cobertura_proyectada_dias = serializers.DecimalField(max_digits=6, decimal_places=1, allow_null=True)
    compra_sugerida = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    proyeccion_diaria = DiaProyectadoSerializer(many=True)
    modelos_evaluados = ModeloEvaluadoSerializer(many=True)


class ProyeccionGuardadaSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    nombre = serializers.CharField()
    tipo = serializers.CharField()
    unidad_medida = serializers.CharField()
    stock_actual = serializers.DecimalField(max_digits=12, decimal_places=2)
    tipo_proyeccion = serializers.CharField()
    modelo_usado = serializers.CharField()
    horizonte_dias = serializers.IntegerField()
    proyeccion_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    promedio_diario = serializers.DecimalField(max_digits=12, decimal_places=2)
    compra_sugerida = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    fecha_generacion = serializers.DateTimeField()
