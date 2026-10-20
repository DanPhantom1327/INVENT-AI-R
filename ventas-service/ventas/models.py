from django.db import models


class Venta(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    producto_id = models.IntegerField()
    # Referencia lógica a:
    # inventario_schema.items_inventario

    cantidad = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    total = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    vendedor_id = models.IntegerField()
    # Referencia lógica a:
    # auth_schema.usuarios

    fecha = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        db_table = "ventas"

        managed = False


    def __str__(self):

        return (
            f"Venta #{self.id} - "
            f"producto {self.producto_id} "
            f"x{self.cantidad}"
        )