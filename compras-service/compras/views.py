from django.core.exceptions import ValidationError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import (
    status,
    permissions
)

from .serializers import (
    CompraSerializer,
    CrearCompraSerializer
)

from .services import CompraService

from common.permissions import TienePermisoDeRol


ROLES_ESCRITURA = [
    "ADMIN",
    "ANALISTA_COMPRAS",
]


ROLES_LECTURA = [
    "ADMIN",
    "GERENTE",
    "ANALISTA_DATOS",
    "ANALISTA_COMPRAS",
    "VENDEDOR",
    "LOGISTICO",
]


class CompraListCreateView(APIView):

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

        materia_prima_id = request.query_params.get(
            "materia_prima_id"
        )

        compras = CompraService.listar_compras(
            materia_prima_id=materia_prima_id
        )

        return Response(
            CompraSerializer(
                compras,
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

        serializer = CrearCompraSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            compra = CompraService.registrar_compra(
                analista_id=request.user.id,
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
            CompraSerializer(compra).data,
            status=status.HTTP_201_CREATED
        )