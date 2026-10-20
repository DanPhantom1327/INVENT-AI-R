from decimal import Decimal

from rest_framework import serializers

from .models import Venta


class VentaSerializer(serializers.ModelSerializer):

    class Meta:

        model = Venta

        fields = [
            "id",
            "producto_id",
            "cantidad",
            "precio_unitario",
            "total",
            "vendedor_id",
            "fecha",
        ]


class CrearVentaSerializer(serializers.Serializer):

    producto_id = serializers.IntegerField()

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