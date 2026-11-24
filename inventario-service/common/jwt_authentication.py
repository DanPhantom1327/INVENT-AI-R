import jwt
from types import SimpleNamespace
from rest_framework import authentication, exceptions
from .jwt_utils import decodificar_token


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

        usuario = SimpleNamespace(
            id=payload["user_id"],
            username=payload["username"],
            rol=payload["rol"],
            is_authenticated=True,
        )
        return (usuario, payload)

    def authenticate_header(self, request):
        # Sin este encabezado, Django REST Framework convierte los 401 en 403 y
        # el frontend no puede distinguir "sesion vencida" (401: renovar el
        # token) de "sin permiso para esta accion" (403: mostrar el rechazo).
        return 'Cookie realm="invent-air"'
