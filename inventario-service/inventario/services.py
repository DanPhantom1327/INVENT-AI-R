#

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from decimal import Decimal

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


def validar_cantidad_inventario(item_id, cantidad):
    try:
        item = ItemInventario.objects.get(id=item_id)
    except ItemInventario.DoesNotExist:
        raise ValidationError(
            "El producto seleccionado no existe."
        )

    cantidad = Decimal(str(cantidad))

    if not cantidad.is_finite() or cantidad <= 0:
        raise ValidationError(
            "La cantidad debe ser mayor que cero."
        )

    if item.tipo == ItemInventario.PRODUCTO_TERMINADO:
        if item.unidad_medida != "unidad":
            raise ValidationError(
                "La pulpa debe manejarse en empaques."
            )

        if cantidad != cantidad.to_integral_value():
            raise ValidationError(
                "La pulpa de 230g solo admite empaques completos."
            )

    return cantidad

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

        cantidad = validar_cantidad_inventario(
        item_id,
        cantidad
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

        cantidad = validar_cantidad_inventario(
        item_id,
        cantidad
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