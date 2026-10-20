#
import getpass

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError

from usuarios.models import Rol, Usuario
from usuarios.services import UsuarioService


class Command(BaseCommand):

    help = "Crea el primer usuario ADMIN del sistema INVENT-AI-R"

    def add_arguments(self, parser):

        parser.add_argument(
            "--username",
            type=str
        )

        parser.add_argument(
            "--email",
            type=str
        )

        parser.add_argument(
            "--nombre",
            type=str
        )

        parser.add_argument(
            "--password",
            type=str
        )

    def handle(self, *args, **options):

        if Usuario.objects.filter(
            rol__nombre=Rol.ADMIN
        ).exists():

            self.stdout.write(
                self.style.WARNING(
                    "Ya existe al menos un usuario ADMIN."
                )
            )

            if input(
                "¿Crear de todas formas otro ADMIN? (s/N): "
            ).strip().lower() != "s":
                return

        username = (
            options.get("username")
            or input("Username: ").strip()
        )

        email = (
            options.get("email")
            or input("Email: ").strip()
        )

        nombre_completo = (
            options.get("nombre")
            or input("Nombre completo: ").strip()
        )

        password = (
            options.get("password")
            or getpass.getpass("Password: ")
        )

        if len(password) < 8:
            raise CommandError(
                "La contraseña debe tener al menos 8 caracteres"
            )

        try:

            usuario = UsuarioService.crear_usuario(
                nombre_completo=nombre_completo,
                username=username,
                email=email,
                rol_nombre=Rol.ADMIN,
                password_temporal=password,
            )

        except ValidationError as e:

            raise CommandError(str(e))

        self.stdout.write(
            self.style.SUCCESS(
                f"Usuario ADMIN '{usuario.username}' "
                f"creado correctamente (id={usuario.id})."
            )
        )