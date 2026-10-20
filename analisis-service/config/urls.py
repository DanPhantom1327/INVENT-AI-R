from django.urls import path, include

urlpatterns = [
    path("analisis/", include("analisis.urls")),
]
