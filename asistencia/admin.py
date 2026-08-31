from django.contrib import admin

from .models import (
    Alumno,
    Materia,
    HorarioClase,
    ClaseActiva,
    Asistencia,
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

    search_fields = (
        "cedula",
        "apellidos",
        "nombres",
        "uid_rfid",
    )

    list_filter = (
        "curso",
        "turno",
        "activo",
    )

    ordering = (
        "apellidos",
        "nombres",
    )

    list_per_page = 50


# ============================================================
# MATERIAS
# ============================================================

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):

    list_display = (
        "nombre",
        "activo",
    )

    search_fields = (
        "nombre",
    )

    list_filter = (
        "activo",
    )

    ordering = (
        "nombre",
    )


# ============================================================
# HORARIOS DE CLASE
# ============================================================

@admin.register(HorarioClase)
class HorarioClaseAdmin(admin.ModelAdmin):

    list_display = (
        "anio_lectivo",
        "curso",
        "dia_semana",
        "hora_inicio",
        "hora_fin",
        "materia",
        "activo",
    )

    list_filter = (
        "anio_lectivo",
        "curso",
        "dia_semana",
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
# CLASES ACTIVAS
# ============================================================

@admin.register(ClaseActiva)
class ClaseActivaAdmin(admin.ModelAdmin):

    list_display = (
        "materia",
        "activa",
        "iniciada",
        "finalizada",
    )

    list_filter = (
        "activa",
        "materia",
    )

    search_fields = (
        "materia__nombre",
    )

    ordering = (
        "-iniciada",
    )


# ============================================================
# ASISTENCIAS
#
# NUEVA LÓGICA:
# - UNA ENTRADA POR DÍA
# - UNA SALIDA POR DÍA
# ============================================================

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):

    list_display = (
        "fecha",
        "alumno",
        "hora_entrada",
        "hora_salida",
        "estado_jornada",
    )

    search_fields = (
        "alumno__cedula",
        "alumno__apellidos",
        "alumno__nombres",
    )

    list_filter = (
        "fecha",
        "alumno__curso",
    )

    ordering = (
        "-fecha",
        "hora_entrada",
    )

    readonly_fields = (
        "estado_jornada",
    )

    list_per_page = 50

    @admin.display(
        description="Estado"
    )
    def estado_jornada(self, obj):

        if obj.hora_entrada and obj.hora_salida:
            return "JORNADA COMPLETA"

        if obj.hora_entrada:
            return "EN EL COLEGIO"

        return "SIN REGISTRO"