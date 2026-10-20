#

from decimal import Decimal
from rest_framework import serializers

from .models import (
    ItemInventario,
    MovimientoInventario
)


class ItemInventarioSerializer(serializers.ModelSerializer):

    class Meta:

        model = ItemInventario

        fields = [
            "id",
            "tipo",
            "nombre",
            "unidad_medida",
            "stock_actual",
            "umbral_dias_cobertura",
            "activo",
            "fecha_creacion",
        ]


class CrearItemSerializer(serializers.Serializer):

    tipo = serializers.ChoiceField(
        choices=[
            ItemInventario.MATERIA_PRIMA,
            ItemInventario.PRODUCTO_TERMINADO,
        ]
    )

    nombre = serializers.CharField(
        max_length=150
    )

    unidad_medida = serializers.CharField(
        max_length=20
    )

    umbral_dias_cobertura = serializers.IntegerField(
        required=False,
        allow_null=True
    )


class MovimientoSerializer(serializers.ModelSerializer):

    class Meta:

        model = MovimientoInventario

        fields = [
            "id",
            "item",
            "tipo_movimiento",
            "efecto",
            "cantidad",
            "motivo_ajuste",
            "usuario_id",
            "referencia",
            "fecha",
        ]


class CrearMovimientoSerializer(serializers.Serializer):

    item_id = serializers.IntegerField()

    tipo_movimiento = serializers.ChoiceField(
        choices=[
            MovimientoInventario.ENTRADA,
            MovimientoInventario.SALIDA,
        ]
    )

    cantidad = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01")
    )

    referencia = serializers.CharField(
        required=False,
        allow_blank=True
    )


class CrearAjusteSerializer(serializers.Serializer):

    item_id = serializers.IntegerField()

    cantidad = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01")
    )

    efecto = serializers.ChoiceField(
        choices=[
            MovimientoInventario.SUMA,
            MovimientoInventario.RESTA,
        ]
    )

    motivo_ajuste = serializers.ChoiceField(
        choices=MovimientoInventario.MOTIVOS_AJUSTE
    )

    referencia = serializers.CharField(
        required=False,
        allow_blank=True
    )