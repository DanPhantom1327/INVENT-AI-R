# CRUD de ítems y movimientos

from django.core.exceptions import ValidationError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import ItemInventario

from .serializers import (
    ItemInventarioSerializer,
    CrearItemSerializer,
    MovimientoSerializer,
    CrearMovimientoSerializer,
    CrearAjusteSerializer,
)

from .services import (
    ItemService,
    MovimientoService
)

from common.permissions import TienePermisoDeRol


ROLES_ESCRITURA = [
    "ADMIN",
    "LOGISTICO",
]


ROLES_LECTURA = [
    "ADMIN",
    "GERENTE",
    "ANALISTA_DATOS",
    "ANALISTA_COMPRAS",
    "VENDEDOR",
    "LOGISTICO",
]


class ItemListCreateView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request):

        self.roles_permitidos = ROLES_LECTURA

        if not TienePermisoDeRol().has_permission(
            request,
            self
        ):

            return Response(
                {
                    "detail": "No autorizado"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        tipo = request.query_params.get("tipo")

        items = ItemService.listar_items(
            tipo=tipo
        )

        return Response(
            ItemInventarioSerializer(
                items,
                many=True
            ).data
        )

    def post(self, request):

        self.roles_permitidos = ROLES_ESCRITURA

        if not TienePermisoDeRol().has_permission(
            request,
            self
        ):

            return Response(
                {
                    "detail": "No autorizado"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CrearItemSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        item = ItemService.crear_item(
            **serializer.validated_data
        )

        return Response(
            ItemInventarioSerializer(item).data,
            status=status.HTTP_201_CREATED
        )


class MovimientoListCreateView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request):

        self.roles_permitidos = ROLES_LECTURA

        if not TienePermisoDeRol().has_permission(
            request,
            self
        ):

            return Response(
                {
                    "detail": "No autorizado"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        item_id = request.query_params.get(
            "item_id"
        )

        movimientos = MovimientoService.historial(
            item_id=item_id
        )

        return Response(
            MovimientoSerializer(
                movimientos,
                many=True
            ).data
        )

    def post(self, request):

        self.roles_permitidos = ROLES_ESCRITURA

        if not TienePermisoDeRol().has_permission(
            request,
            self
        ):

            return Response(
                {
                    "detail": "No autorizado"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CrearMovimientoSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            movimiento = (
                MovimientoService.registrar_movimiento(
                    usuario_id=request.user.id,
                    **serializer.validated_data,
                )
            )

        except ValidationError as e:

            return Response(
                {
                    "detail": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            MovimientoSerializer(movimiento).data,
            status=status.HTTP_201_CREATED
        )


class AjusteCreateView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    roles_permitidos = ROLES_ESCRITURA

    def post(self, request):

        if not TienePermisoDeRol().has_permission(
            request,
            self
        ):

            return Response(
                {
                    "detail": "No autorizado"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CrearAjusteSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            movimiento = (
                MovimientoService.registrar_ajuste(
                    usuario_id=request.user.id,
                    **serializer.validated_data,
                )
            )

        except ValidationError as e:

            return Response(
                {
                    "detail": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            MovimientoSerializer(movimiento).data,
            status=status.HTTP_201_CREATED
        )
