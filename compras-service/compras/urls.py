from django.urls import path
from .views import CompraListCreateView

urlpatterns = [ path("compras", CompraListCreateView.as_view(), name="compras"), ]