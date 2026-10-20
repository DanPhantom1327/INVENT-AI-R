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
