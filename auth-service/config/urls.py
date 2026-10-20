#conecta las rutas principales del proyecto con las rutas que creamos anteriormente en usuarios/urls.py.
from django.urls import path, include


urlpatterns = [
    path(
        "auth/",
        include("usuarios.urls")
    ),
]
