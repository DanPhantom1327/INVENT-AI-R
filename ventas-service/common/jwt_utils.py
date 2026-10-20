import jwt

from django.conf import settings


def _load_key(path):

    with open(path, "rb") as f:
        return f.read()


def decodificar_token(
    token,
    tipo_esperado="access"
):

    clave_publica = _load_key(
        settings.JWT_PUBLIC_KEY_PATH
    )

    payload = jwt.decode(
        token,
        clave_publica,
        algorithms=["RS256"],
        issuer=settings.JWT_ISSUER
    )

    if payload.get("type") != tipo_esperado:

        raise jwt.InvalidTokenError(
            f"Se esperaba un token de tipo "
            f"'{tipo_esperado}'"
        )

    return payload