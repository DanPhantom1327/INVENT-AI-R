
from decimal import Decimal
from rest_framework import serializers
from .models import Venta


PRECIO_PULPA_230G = Decimal("2800.00")


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
    producto_id = serializers.IntegerField(min_value=1)

    cantidad = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("1.00")
    )

    precio_unitario = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=PRECIO_PULPA_230G
    )

    def validate_cantidad(self, value):
        if value != value.to_integral_value():
            raise serializers.ValidationError(
                "La pulpa de 230g se vende por empaques completos."
            )
        return value

    def validate_precio_unitario(self, value):
        if value != PRECIO_PULPA_230G:
            raise serializers.ValidationError(
                "El precio de cada empaque es $2.800 COP."
            )
        return value
