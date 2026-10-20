#UsuarioService --> busca el rol, crea el usuario y obliga a que cambie la contraseña temporal.
#AuthService --> verifica usuario y contraseña, Genera access_token y refresh_token, recibe el refresh token y genera un nuevo access token.

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError

from .models import Usuario, Rol

from common.jwt_utils import (
    generar_access_token,
    generar_refresh_token,
    decodificar_token
)


class AuthService:

    @staticmethod
    def login(username, password):

        try:
            usuario = Usuario.objects.select_related("rol").get(
                username=username,
                activo=True
            )

        except Usuario.DoesNotExist:
            raise ValidationError("Credenciales invalidas")

        if not check_password(
            password,
            usuario.password_hash
        ):
            raise ValidationError("Credenciales invalidas")

        access_token = generar_access_token(usuario)
        refresh_token = generar_refresh_token(usuario)

        return usuario, access_token, refresh_token

    @staticmethod
    def refrescar_access_token(refresh_token):

        payload = decodificar_token(
            refresh_token,
            tipo_esperado="refresh"
        )

        try:
            usuario = Usuario.objects.select_related("rol").get(
                id=payload["user_id"],
                activo=True
            )

        except Usuario.DoesNotExist:
            raise ValidationError(
                "Usuario no encontrado o inactivo"
            )

        return generar_access_token(usuario)


class UsuarioService:

    @staticmethod
    def crear_usuario(
        nombre_completo,
        username,
        email,
        rol_nombre,
        password_temporal
    ):

        try:
            rol = Rol.objects.get(
                nombre=rol_nombre
            )

        except Rol.DoesNotExist:
            raise ValidationError(
                f"Rol '{rol_nombre}' no existe"
            )

        usuario = Usuario.objects.create_user(
            username=username,
            email=email,
            nombre_completo=nombre_completo,
            rol=rol,
            password=password_temporal,
        )

        usuario.debe_cambiar_password = True

        usuario.save(
            update_fields=["debe_cambiar_password"]
        )

        return usuario