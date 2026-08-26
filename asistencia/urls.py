from django.urls import path
from . import views


urlpatterns = [

    path(
        "pantalla/",
        views.pantalla_asistencia,
        name="pantalla_asistencia"
    ),

    path(
        "api/estado/",
        views.estado_pantalla,
        name="estado_pantalla"
    ),

    path(
        "prueba/<str:cedula>/",
        views.probar_asistencia,
        name="probar_asistencia"
    ),

]