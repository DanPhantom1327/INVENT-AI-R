from decimal import Decimal

from rest_framework import serializers

from .models import Compra


class CompraSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = Compra

        fields = [
            "id",
            "materia_prima_id",
            "cantidad",
            "precio_unitario",
            "total",
            "proveedor",
            "analista_id",
            "fecha",
        ]


class CrearCompraSerializer(
    serializers.Serializer
):

    materia_prima_id = serializers.IntegerField()

    cantidad = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01")
    )

    precio_unitario = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0")
    )

    proveedor = serializers.CharField(
        max_length=150
    )