from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .models import Venta


class VentaService:

    @staticmethod
    def registrar_venta(
        producto_id,
        cantidad,
        precio_unitario,
        vendedor_id
    ):

        total = cantidad * precio_unitario

        try:

            with transaction.atomic():

                venta = Venta.objects.create(
                    producto_id=producto_id,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    total=total,
                    vendedor_id=vendedor_id,
                )

        except IntegrityError as e:
            # El trigger de PostgreSQL rechaza la venta
            # si no es PRODUCTO_TERMINADO o si no hay
            # stock suficiente.

            raise ValidationError(
                f"No se pudo registrar la venta: {e}"
            )

        return venta


    @staticmethod
    def listar_ventas(
        producto_id=None
    ):

        qs = Venta.objects.all()

        if producto_id:

            qs = qs.filter(
                producto_id=producto_id
            )

        return qs.order_by(
            "-fecha"
        )