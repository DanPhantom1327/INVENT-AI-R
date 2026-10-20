"""Presenter (capa MVP): recibe HTTP, valida permisos, delega en services."""
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import TienePermisoDeRol

from . import calculos
from .serializers import (
    AlertaSerializer, CoberturaCalculadaSerializer, CoberturaGuardadaSerializer,
    GenerarProyeccionSerializer, ProyeccionGuardadaSerializer,
    ProyeccionResultadoSerializer,
)
from .services import AlertaService, CoberturaService, ProyeccionService

ROLES_CALCULO = ["ADMIN", "ANALISTA_DATOS"]
ROLES_LECTURA = ["ADMIN", "GERENTE", "ANALISTA_DATOS", "ANALISTA_COMPRAS", "LOGISTICO"]
ESTADOS_VALIDOS = ("ACTIVA", "RESUELTA")


class CalcularCoberturaView(APIView):
    """POST /analisis/cobertura/calcular"""
    permission_classes = [permissions.IsAuthenticated, TienePermisoDeRol]
    roles_permitidos = ROLES_CALCULO

    def post(self, request):
        resultados = CoberturaService.calcular_y_alertar()
        return Response({
            "ventana_dias": calculos.VENTANA_DIAS,
            "resultados": CoberturaCalculadaSerializer(resultados, many=True).data,
        })


class CoberturaView(APIView):
    """GET /analisis/cobertura : ultima cobertura calculada de cada item"""
    permission_classes = [permissions.IsAuthenticated, TienePermisoDeRol]
    roles_permitidos = ROLES_LECTURA

    def get(self, request):
        filas = CoberturaService.ultima_cobertura()
        return Response(CoberturaGuardadaSerializer(filas, many=True).data)


class AlertaListView(APIView):
    """GET /analisis/alertas?estado=ACTIVA|RESUELTA"""
    permission_classes = [permissions.IsAuthenticated, TienePermisoDeRol]
    roles_permitidos = ROLES_LECTURA

    def get(self, request):
        estado = request.query_params.get("estado")
        if estado and estado not in ESTADOS_VALIDOS:
            return Response(
                {"detail": "estado debe ser ACTIVA o RESUELTA"},
                status=status.HTTP_400_BAD_REQUEST)
        return Response(AlertaSerializer(AlertaService.listar(estado), many=True).data)


ROLES_LECTURA_PROYECCION = ["ADMIN", "GERENTE", "ANALISTA_DATOS", "ANALISTA_COMPRAS"]


class GenerarProyeccionView(APIView):
    """POST /analisis/proyecciones/generar   cuerpo opcional: {"horizonte_dias": 14}"""
    permission_classes = [permissions.IsAuthenticated, TienePermisoDeRol]
    roles_permitidos = ROLES_CALCULO

    def post(self, request):
        entrada = GenerarProyeccionSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        horizonte = entrada.validated_data["horizonte_dias"]
        resultados = ProyeccionService.generar(horizonte)
        return Response({
            "horizonte_dias": horizonte,
            "resultados": ProyeccionResultadoSerializer(resultados, many=True).data,
        })


class ProyeccionListView(APIView):
    """GET /analisis/proyecciones : ultima proyeccion guardada de cada item"""
    permission_classes = [permissions.IsAuthenticated, TienePermisoDeRol]
    roles_permitidos = ROLES_LECTURA_PROYECCION

    def get(self, request):
        filas = ProyeccionService.ultimas()
        return Response(ProyeccionGuardadaSerializer(filas, many=True).data)
