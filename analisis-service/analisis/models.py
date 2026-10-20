"""
Model (capa MVP). Solo las tablas PROPIAS de este servicio (analisis_schema).
managed = False: las crea el script DDL de la Fase 3.
item_id es un entero (no ForeignKey) porque el item vive en inventario_schema,
que pertenece a otro servicio; la integridad la garantiza la FK real en la BD.
"""
from django.db import models


class CoberturaStock(models.Model):
    id = models.AutoField(primary_key=True)
    item_id = models.IntegerField()
    dias_cobertura_estimados = models.DecimalField(max_digits=6, decimal_places=1)
    fecha_calculo = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cobertura_stock"
        managed = False


class Alerta(models.Model):
    ACTIVA = "ACTIVA"
    RESUELTA = "RESUELTA"

    id = models.AutoField(primary_key=True)
    item_id = models.IntegerField()
    tipo_alerta = models.CharField(max_length=30)
    nivel_severidad = models.CharField(max_length=10)
    mensaje = models.TextField()
    estado = models.CharField(max_length=15, default="ACTIVA")
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "alertas"
        managed = False


class Proyeccion(models.Model):
    DEMANDA = "DEMANDA"
    NECESIDAD_MATERIA_PRIMA = "NECESIDAD_MATERIA_PRIMA"

    id = models.AutoField(primary_key=True)
    item_id = models.IntegerField()
    tipo_proyeccion = models.CharField(max_length=30)
    valor_proyectado = models.DecimalField(max_digits=12, decimal_places=2)
    horizonte_dias = models.IntegerField()
    modelo_usado = models.CharField(max_length=50)
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "proyecciones"
        managed = False
