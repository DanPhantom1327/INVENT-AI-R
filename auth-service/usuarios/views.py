#LoginView → inicia sesión y crea las cookies JWT.
#RefreshView → renueva el access_token.
#LogoutView → elimina las cookies y cierra sesión.
#MeView → devuelve los datos del usuario autenticado.
#CambiarPasswordView → permite cambiar la contraseña.
#UsuarioAdminView → permite al ADMIN crear nuevos usuarios.

from django.conf import settings
from django.core.exceptions import ValidationError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .serializers import (
    LoginSerializer,
    UsuarioSerializer,
    CrearUsuarioSerializer,
    CambiarPasswordSerializer,
)

from .services import AuthService, UsuarioService
from .models import Rol
from .permissions import TienePermisoDeRol


def _set_cookie(response, nombre, valor, max_age_segundos):

    response.set_cookie(
        key=nombre,
        value=valor,
        max_age=max_age_segundos,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )


class LoginView(APIView):

    permission_classes = [permissions.AllowAny]

    def post(self, request):

        serializer = LoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            usuario, access_token, refresh_token = AuthService.login(
                **serializer.validated_data
            )

        except ValidationError:

            return Response(
                {
                    "detail": "Credenciales invalidas"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        response = Response(
            {
                "usuario": UsuarioSerializer(usuario).data,
                "debe_cambiar_password": usuario.debe_cambiar_password
            },
            status=status.HTTP_200_OK,
        )

        _set_cookie(
            response,
            "access_token",
            access_token,
            settings.JWT_ACCESS_TOKEN_MINUTES * 60
        )

        _set_cookie(
            response,
            "refresh_token",
            refresh_token,
            settings.JWT_REFRESH_TOKEN_DAYS * 86400
        )

        return response


class RefreshView(APIView):

    permission_classes = [permissions.AllowAny]

    def post(self, request):

        refresh_token = request.COOKIES.get(
            "refresh_token"
        )

        if not refresh_token:

            return Response(
                {
                    "detail": "No hay refresh token"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:

            nuevo_access_token = (
                AuthService.refrescar_access_token(
                    refresh_token
                )
            )

        except Exception:

            return Response(
                {
                    "detail": "Refresh token invalido o expirado"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        response = Response(
            {
                "detail": "Token renovado"
            },
            status=status.HTTP_200_OK
        )

        _set_cookie(
            response,
            "access_token",
            nuevo_access_token,
            settings.JWT_ACCESS_TOKEN_MINUTES * 60
        )

        return response


class LogoutView(APIView):

    def post(self, request):

        response = Response(
            {
                "detail": "Sesion cerrada"
            },
            status=status.HTTP_200_OK
        )

        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response


class MeView(APIView):

    def get(self, request):

        return Response(
            UsuarioSerializer(request.user).data
        )


class CambiarPasswordView(APIView):

    def post(self, request):

        serializer = CambiarPasswordSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            UsuarioService.cambiar_password(
                request.user,
                **serializer.validated_data
            )

        except ValidationError as e:

            return Response(
                {
                    "detail": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "detail": "Contrasena actualizada"
            }
        )


class UsuarioAdminView(APIView):

    permission_classes = [
        permissions.IsAuthenticated,
        TienePermisoDeRol
    ]

    roles_permitidos = [
        Rol.ADMIN
    ]

    def post(self, request):

        serializer = CrearUsuarioSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            usuario = UsuarioService.crear_usuario(
                **serializer.validated_data
            )

        except ValidationError as e:

            return Response(
                {
                    "detail": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            UsuarioSerializer(usuario).data,
            status=status.HTTP_201_CREATED
        )