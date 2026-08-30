from django.contrib import admin
from django.urls import path

from asistencia import views


urlpatterns = [

    path(
        "admin/",
        admin.site.urls
    ),

    path(
        "pantalla/",
        views.pantalla,
        name="pantalla_asistencia"
    ),

    path(
        "api/asistencia/",
        views.registrar_rfid,
        name="registrar_rfid"
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