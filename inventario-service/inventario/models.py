#Django no va a crear, modificar ni eliminar estas tablas mediante migraciones.
# Django simplemente las utilizará como representación de tablas que ya existen en PostgreSQL

from django.db import models


class ItemInventario(models.Model):

    MATERIA_PRIMA = "MATERIA_PRIMA"
    PRODUCTO_TERMINADO = "PRODUCTO_TERMINADO"

    TIPO_CHOICES = [
        (MATERIA_PRIMA, "Materia prima"),
        (PRODUCTO_TERMINADO, "Producto terminado"),
    ]

    id = models.AutoField(
        primary_key=True
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES
    )

    nombre = models.CharField(
        max_length=150
    )

    unidad_medida = models.CharField(
        max_length=20
    )

    stock_actual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    umbral_dias_cobertura = models.IntegerField(
        null=True,
        blank=True
    )

    activo = models.BooleanField(
        default=True
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        db_table = "items_inventario"

        managed = False

    def __str__(self):

        return f"{self.nombre} ({self.tipo})"


class MovimientoInventario(models.Model):

    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"

    TIPO_CHOICES = [
        (ENTRADA, "Entrada"),
        (SALIDA, "Salida"),
        (AJUSTE, "Ajuste"),
    ]

    SUMA = "SUMA"
    RESTA = "RESTA"

    EFECTO_CHOICES = [
        (SUMA, "Suma"),
        (RESTA, "Resta"),
    ]

    MOTIVOS_AJUSTE = [
        "MERMA",
        "ERROR_CONTEO",
        "DEVOLUCION",
    ]

    id = models.AutoField(
        primary_key=True
    )

    item = models.ForeignKey(
        ItemInventario,
        on_delete=models.PROTECT,
        db_column="item_id",
        related_name="movimientos"
    )

    tipo_movimiento = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES
    )

    efecto = models.CharField(
        max_length=5,
        choices=EFECTO_CHOICES
    )

    cantidad = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    motivo_ajuste = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    usuario_id = models.IntegerField()

    referencia = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        db_table = "movimientos_inventario"

        managed = False

    def __str__(self):

        return (
            f"{self.tipo_movimiento} "
            f"{self.cantidad} -> item {self.item_id}"
        )