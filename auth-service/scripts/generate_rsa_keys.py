import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


KEYS_DIR = os.path.join(os.path.dirname(__file__), "..", "keys")


def generate_keys():
    os.makedirs(KEYS_DIR, exist_ok=True)

    # Generar clave privada
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # Obtener clave pública
    public_key = private_key.public_key()

    # Convertir clave privada a formato PEM
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Convertir clave pública a formato PEM
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Guardar clave privada
    with open(os.path.join(KEYS_DIR, "private_key.pem"), "wb") as f:
        f.write(private_pem)

    # Guardar clave pública
    with open(os.path.join(KEYS_DIR, "public_key.pem"), "wb") as f:
        f.write(public_pem)

    print(f"Claves generadas en: {KEYS_DIR}")


if __name__ == "__main__":
    generate_keys()