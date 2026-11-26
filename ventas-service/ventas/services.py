
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .models import Venta


PRECIO_PULPA_230G = Decimal("2800.00")


class VentaService:

    @staticmethod
    def registrar_venta(
        producto_id,
        cantidad,
        precio_unitario,
        vendedor_id
    ):
        cantidad = Decimal(str(cantidad))

        if cantidad <= 0 or cantidad != cantidad.to_integral_value():
            raise ValidationError(
                "Solo se permiten empaques completos de 230g."
            )

        if Decimal(str(precio_unitario)) != PRECIO_PULPA_230G:
            raise ValidationError(
                "El precio unitario obligatorio es $2.800 COP."
            )

        total = cantidad * PRECIO_PULPA_230G

        try:
            with transaction.atomic():
                venta = Venta.objects.create(
                    producto_id=producto_id,
                    cantidad=cantidad,
                    precio_unitario=PRECIO_PULPA_230G,
                    total=total,
                    vendedor_id=vendedor_id,
                )

        except IntegrityError as e:
            raise ValidationError(
                f"No se pudo registrar la venta: {e}"
            )

        return venta

    @staticmethod
    def listar_ventas(producto_id=None):
        qs = Venta.objects.all()

        if producto_id:
            qs = qs.filter(producto_id=producto_id)

        return qs.order_by("-fecha")
