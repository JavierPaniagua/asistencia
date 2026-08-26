from django.contrib import admin
from .models import Alumno, TarjetaRFID, Asistencia


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = (
        "cedula",
        "apellido",
        "nombre",
        "curso",
        "activo",
    )

    search_fields = (
        "cedula",
        "apellido",
        "nombre",
    )

    list_filter = (
        "curso",
        "activo",
    )


@admin.register(TarjetaRFID)
class TarjetaRFIDAdmin(admin.ModelAdmin):
    list_display = (
        "uid",
        "alumno",
        "activa",
    )

    search_fields = (
        "uid",
        "alumno__cedula",
        "alumno__nombre",
        "alumno__apellido",
    )

    list_filter = (
        "activa",
    )


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = (
        "alumno",
        "fecha",
        "hora",
    )

    search_fields = (
        "alumno__cedula",
        "alumno__nombre",
        "alumno__apellido",
    )

    list_filter = (
        "fecha",
    )