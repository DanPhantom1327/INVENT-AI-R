# URLs — conectando los endpoints de inventario

from django.urls import path

from .views import (
    ItemListCreateView,
    MovimientoListCreateView,
    AjusteCreateView,
)


urlpatterns = [

    path(
        "items",
        ItemListCreateView.as_view(),
        name="items"
    ),

    path(
        "movimientos",
        MovimientoListCreateView.as_view(),
        name="movimientos"
    ),

    path(
        "movimientos/ajuste",
        AjusteCreateView.as_view(),
        name="ajuste"
    ),

]