from django.urls import path

from .views import (
    AlertaListView, CalcularCoberturaView, CoberturaView,
    GenerarProyeccionView, ProyeccionListView,
)

urlpatterns = [
    path("cobertura", CoberturaView.as_view(), name="cobertura"),
    path("cobertura/calcular", CalcularCoberturaView.as_view(), name="cobertura-calcular"),
    path("alertas", AlertaListView.as_view(), name="alertas"),
    path("proyecciones", ProyeccionListView.as_view(), name="proyecciones"),
    path("proyecciones/generar", GenerarProyeccionView.as_view(), name="proyecciones-generar"),
]
