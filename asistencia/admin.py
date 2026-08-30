from django.contrib import admin

from .models import Alumno, Asistencia


# ============================================================
# ADMIN ALUMNOS
# ============================================================

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):

    list_display = (
        "cedula",
        "nombre",
        "curso",
        "uid_rfid",
        "activo",
    )

    search_fields = (
        "cedula",
        "nombre",
        "curso",
        "uid_rfid",
    )

    list_filter = (
        "curso",
        "activo",
    )

    ordering = (
        "nombre",
    )


# ============================================================
# ADMIN ASISTENCIAS
# ============================================================

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):

    list_display = (
        "alumno",
        "fecha",
        "hora",
        "estado",
    )

    search_fields = (
        "alumno__cedula",
        "alumno__nombre",
        "alumno__uid_rfid",
    )

    list_filter = (
        "fecha",
        "estado",
        "alumno__curso",
    )

    ordering = (
        "-fecha",
        "-hora",
    )