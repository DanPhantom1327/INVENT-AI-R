#se encarga de conectar las rutas con las vistas
from django.urls import path

from .views import (
    LoginView,
    RefreshView,
    LogoutView,
    MeView,
    CambiarPasswordView,
    UsuarioAdminView,
)


urlpatterns = [

    path(
        "login",
        LoginView.as_view(),
        name="login"
    ),

    path(
        "refresh",
        RefreshView.as_view(),
        name="refresh"
    ),

    path(
        "logout",
        LogoutView.as_view(),
        name="logout"
    ),

    path(
        "me",
        MeView.as_view(),
        name="me"
    ),

    path(
        "cambiar-password",
        CambiarPasswordView.as_view(),
        name="cambiar-password"
    ),

    path(
        "usuarios",
        UsuarioAdminView.as_view(),
        name="crear-usuario"
    ),
]