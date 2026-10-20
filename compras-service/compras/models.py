from django.db import models


class Compra(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    materia_prima_id = models.IntegerField()
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

    proveedor = models.CharField(
        max_length=150
    )

    analista_id = models.IntegerField()
    # Referencia lógica a:
    # auth_schema.usuarios

    fecha = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        db_table = "compras"

        managed = False


    def __str__(self):

        return (
            f"Compra #{self.id} - "
            f"materia prima {self.materia_prima_id} "
            f"x{self.cantidad}"
        )