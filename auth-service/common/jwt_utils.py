import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings


def _load_key(path):
    with open(path, "rb") as f:
        return f.read()


def generar_access_token(usuario):
    ahora = datetime.now(timezone.utc)

    payload = {
        "user_id": usuario.id,
        "username": usuario.username,
        "rol": usuario.rol.nombre,
        "iss": settings.JWT_ISSUER,
        "iat": ahora,
        "exp": ahora + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_MINUTES
        ),
        "type": "access",
    }

    clave_privada = _load_key(settings.JWT_PRIVATE_KEY_PATH)

    return jwt.encode(
        payload,
        clave_privada,
        algorithm=settings.JWT_ALGORITHM
    )


def generar_refresh_token(usuario):
    ahora = datetime.now(timezone.utc)

    payload = {
        "user_id": usuario.id,
        "iss": settings.JWT_ISSUER,
        "iat": ahora,
        "exp": ahora + timedelta(
            days=settings.JWT_REFRESH_TOKEN_DAYS
        ),
        "type": "refresh",
    }

    clave_privada = _load_key(settings.JWT_PRIVATE_KEY_PATH)

    return jwt.encode(
        payload,
        clave_privada,
        algorithm=settings.JWT_ALGORITHM
    )


def decodificar_token(token, tipo_esperado="access"):
    clave_publica = _load_key(settings.JWT_PUBLIC_KEY_PATH)

    payload = jwt.decode(
        token,
        clave_publica,
        algorithms=[settings.JWT_ALGORITHM],
        issuer=settings.JWT_ISSUER,
    )

    if payload.get("type") != tipo_esperado:
        raise jwt.InvalidTokenError(
            f"Se esperaba un token de tipo '{tipo_esperado}'"
        )

    return payload