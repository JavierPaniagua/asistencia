from django.contrib import admin

from .models import (
    Alumno,
    Asistencia,
    Materia,
    HorarioClase,
    ClaseActiva,
)


# ============================================================
# ALUMNOS
# ============================================================

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):

    list_display = (
        "cedula",
        "apellidos",
        "nombres",
        "curso",
        "turno",
        "uid_rfid",
        "activo",
    )

    list_filter = (
        "activo",
        "turno",
    )

    search_fields = (
        "cedula",
        "nombres",
        "apellidos",
        "uid_rfid",
    )

    ordering = (
        "apellidos",
        "nombres",
    )


# ============================================================
# MATERIAS
# ============================================================

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "nombre",
        "activo",
    )

    list_filter = (
        "activo",
    )

    search_fields = (
        "nombre",
    )

    ordering = (
        "nombre",
    )


# ============================================================
# HORARIOS
# ============================================================

@admin.register(HorarioClase)
class HorarioClaseAdmin(admin.ModelAdmin):

    list_display = (
        "anio_lectivo",
        "dia_semana",
        "hora_inicio",
        "hora_fin",
        "curso",
        "materia",
        "activo",
    )

    list_filter = (
        "anio_lectivo",
        "dia_semana",
        "curso",
        "materia",
        "activo",
    )

    search_fields = (
        "curso",
        "materia__nombre",
    )

    ordering = (
        "dia_semana",
        "hora_inicio",
    )


# ============================================================
# CLASE MANUAL
# ============================================================

@admin.register(ClaseActiva)
class ClaseActivaAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "materia",
        "activa",
        "iniciada",
        "finalizada",
    )

    list_filter = (
        "activa",
        "materia",
    )

    ordering = (
        "-iniciada",
    )


# ============================================================
# ASISTENCIAS
# ============================================================

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):

    list_display = (
        "alumno",
        "materia",
        "fecha",
        "hora",
    )

    list_filter = (
        "materia",
        "fecha",
    )

    search_fields = (
        "alumno__cedula",
        "alumno__nombres",
        "alumno__apellidos",
        "materia__nombre",
    )

    date_hierarchy = "fecha"

    ordering = (
        "-fecha",
        "-hora",
    )