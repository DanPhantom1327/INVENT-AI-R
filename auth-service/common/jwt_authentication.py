import jwt
from rest_framework import authentication, exceptions
from .jwt_utils import decodificar_token
from usuarios.models import Usuario


class CookieJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get("access_token")
        if not token:
            return None

        try:
            payload = decodificar_token(token, tipo_esperado="access")
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("El token ha expirado")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Token invalido")

        try:
            usuario = Usuario.objects.select_related("rol").get(
                id=payload["user_id"], activo=True
            )
        except Usuario.DoesNotExist:
            raise exceptions.AuthenticationFailed("Usuario no encontrado o inactivo")

        return (usuario, payload)

    def authenticate_header(self, request):
        # Ver nota en los demas servicios: permite que DRF responda 401 y no 403.
        return 'Cookie realm="invent-air"'
