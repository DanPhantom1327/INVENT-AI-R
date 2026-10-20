#

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .models import (
    ItemInventario,
    MovimientoInventario
)


class ItemService:

    @staticmethod
    def crear_item(
        tipo,
        nombre,
        unidad_medida,
        umbral_dias_cobertura=None
    ):

        return ItemInventario.objects.create(
            tipo=tipo,
            nombre=nombre,
            unidad_medida=unidad_medida,
            umbral_dias_cobertura=umbral_dias_cobertura,
        )

    @staticmethod
    def listar_items(tipo=None):

        qs = ItemInventario.objects.filter(
            activo=True
        )

        if tipo:
            qs = qs.filter(
                tipo=tipo
            )

        return qs.order_by("nombre")


class MovimientoService:

    @staticmethod
    def registrar_movimiento(
        item_id,
        tipo_movimiento,
        cantidad,
        usuario_id,
        referencia=None
    ):

        efecto = {
            MovimientoInventario.ENTRADA:
                MovimientoInventario.SUMA,

            MovimientoInventario.SALIDA:
                MovimientoInventario.RESTA,

        }.get(tipo_movimiento)

        if efecto is None:

            raise ValidationError(
                "Para movimientos AJUSTE usa "
                "registrar_ajuste(), no este metodo"
            )

        try:

            with transaction.atomic():

                movimiento = (
                    MovimientoInventario.objects.create(
                        item_id=item_id,
                        tipo_movimiento=tipo_movimiento,
                        efecto=efecto,
                        cantidad=cantidad,
                        usuario_id=usuario_id,
                        referencia=referencia,
                    )
                )

        except IntegrityError as e:

            raise ValidationError(
                f"No se pudo registrar el movimiento: {e}"
            )

        return movimiento

    @staticmethod
    def registrar_ajuste(
        item_id,
        cantidad,
        efecto,
        motivo_ajuste,
        usuario_id,
        referencia=None
    ):

        if motivo_ajuste not in (
            MovimientoInventario.MOTIVOS_AJUSTE
        ):

            raise ValidationError(
                f"motivo_ajuste invalido: {motivo_ajuste}"
            )

        if efecto not in (
            MovimientoInventario.SUMA,
            MovimientoInventario.RESTA
        ):

            raise ValidationError(
                "efecto debe ser SUMA o RESTA"
            )

        try:

            with transaction.atomic():

                movimiento = (
                    MovimientoInventario.objects.create(
                        item_id=item_id,
                        tipo_movimiento=(
                            MovimientoInventario.AJUSTE
                        ),
                        efecto=efecto,
                        cantidad=cantidad,
                        motivo_ajuste=motivo_ajuste,
                        usuario_id=usuario_id,
                        referencia=referencia,
                    )
                )

        except IntegrityError as e:

            raise ValidationError(
                f"No se pudo registrar el ajuste: {e}"
            )

        return movimiento

    @staticmethod
    def historial(item_id=None):

        qs = (
            MovimientoInventario.objects
            .select_related("item")
            .all()
        )

        if item_id:
            qs = qs.filter(
                item_id=item_id
            )

        return qs.order_by("-fecha")