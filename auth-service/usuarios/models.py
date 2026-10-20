"""
Model (capa MVP) de auth-service.
Ruta: auth-service/usuarios/models.py

managed = False en ambas clases porque las tablas ya las crea el script
DDL de la Fase 3 (invent_air_schema.sql) — Django solo las mapea, no las
gestiona con migraciones.
"""
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.db import models


class Rol(models.Model):
    ADMIN = "ADMIN"
    GERENTE = "GERENTE"
    ANALISTA_DATOS = "ANALISTA_DATOS"
    ANALISTA_COMPRAS = "ANALISTA_COMPRAS"
    VENDEDOR = "VENDEDOR"
    LOGISTICO = "LOGISTICO"

    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "roles"
        managed = False

    def __str__(self):
        return self.nombre


class UsuarioManager(BaseUserManager):
    def create_user(self, username, email, nombre_completo, rol, password=None, **extra):
        if not username or not email:
            raise ValueError("username y email son obligatorios")
        usuario = self.model(
            username=username,
            email=self.normalize_email(email),
            nombre_completo=nombre_completo,
            rol=rol,
            **extra,
        )
        usuario.password_hash = make_password(password)
        usuario.save(using=self._db)
        return usuario


class Usuario(AbstractBaseUser):
    """RF01: solo el ADMIN crea usuarios (logica en usuarios/services.py, Paso 3)."""
    id = models.AutoField(primary_key=True)
    nombre_completo = models.CharField(max_length=150)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=255)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, db_column="rol_id")
    debe_cambiar_password = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "nombre_completo"]

    objects = UsuarioManager()

    # AbstractBaseUser espera un campo 'password'; lo redirigimos a password_hash
    # para que el nombre de columna coincida con el DDL de la Fase 3.
    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, value):
        self.password_hash = value

    class Meta:
        db_table = "usuarios"
        managed = False

    def __str__(self):
        return f"{self.username} ({self.rol.nombre})"
