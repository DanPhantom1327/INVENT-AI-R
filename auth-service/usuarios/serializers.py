#recibe username y password para iniciar sesión.
#CambiarPasswordSerializer → recibe la contraseña actual y la nueva, con mínimo 8 caracteres.
#UsuarioSerializer → devuelve la información del usuario, incluyendo el nombre del rol.
#CrearUsuarioSerializer → valida los datos necesarios para crear un usuario y limita el campo rol a los roles definidos en Rol.

from rest_framework import serializers

from .models import Usuario, Rol


class LoginSerializer(serializers.Serializer):

    username = serializers.CharField()

    password = serializers.CharField(
        write_only=True
    )


class CambiarPasswordSerializer(serializers.Serializer):

    password_actual = serializers.CharField(
        write_only=True
    )

    password_nueva = serializers.CharField(
        write_only=True,
        min_length=8
    )


class UsuarioSerializer(serializers.ModelSerializer):

    rol = serializers.CharField(
        source="rol.nombre",
        read_only=True
    )

    class Meta:

        model = Usuario

        fields = [
            "id",
            "nombre_completo",
            "username",
            "email",
            "rol",
            "debe_cambiar_password",
            "activo",
            "fecha_creacion",
        ]


class CrearUsuarioSerializer(serializers.Serializer):

    nombre_completo = serializers.CharField(
        max_length=150
    )

    username = serializers.CharField(
        max_length=50
    )

    email = serializers.EmailField()

    rol = serializers.ChoiceField(
        choices=[
            Rol.ADMIN,
            Rol.GERENTE,
            Rol.ANALISTA_DATOS,
            Rol.ANALISTA_COMPRAS,
            Rol.VENDEDOR,
            Rol.LOGISTICO,
        ]
    )

    password_temporal = serializers.CharField(
        write_only=True,
        min_length=8
    )