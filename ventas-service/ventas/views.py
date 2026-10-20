from django.core.exceptions import ValidationError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import (
    status,
    permissions
)

from .serializers import (
    VentaSerializer,
    CrearVentaSerializer
)

from .services import VentaService

from common.permissions import TienePermisoDeRol


ROLES_ESCRITURA = [
    "ADMIN",
    "VENDEDOR",
]


ROLES_LECTURA = [
    "ADMIN",
    "GERENTE",
    "ANALISTA_DATOS",
    "ANALISTA_COMPRAS",
    "VENDEDOR",
    "LOGISTICO",
]


class VentaListCreateView(APIView):

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

        producto_id = request.query_params.get(
            "producto_id"
        )

        ventas = VentaService.listar_ventas(
            producto_id=producto_id
        )

        return Response(
            VentaSerializer(
                ventas,
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

        serializer = CrearVentaSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            venta = VentaService.registrar_venta(
                vendedor_id=request.user.id,
                **serializer.validated_data,
            )

        except ValidationError as e:

            return Response(
                {
                    "detail": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            VentaSerializer(venta).data,
            status=status.HTTP_201_CREATED
        )