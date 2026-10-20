from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .models import Compra


class CompraService:

    @staticmethod
    def registrar_compra(
        materia_prima_id,
        cantidad,
        precio_unitario,
        proveedor,
        analista_id
    ):

        total = cantidad * precio_unitario

        try:

            with transaction.atomic():

                compra = Compra.objects.create(
                    materia_prima_id=materia_prima_id,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    total=total,
                    proveedor=proveedor,
                    analista_id=analista_id,
                )

        except IntegrityError as e:

            # El trigger de PostgreSQL rechaza la compra
            # si el item no es MATERIA_PRIMA.

            raise ValidationError(
                f"No se pudo registrar la compra: {e}"
            )

        return compra


    @staticmethod
    def listar_compras(
        materia_prima_id=None
    ):

        qs = Compra.objects.all()

        if materia_prima_id:

            qs = qs.filter(
                materia_prima_id=materia_prima_id
            )

        return qs.order_by(
            "-fecha"
        )