from django.contrib import admin
from django.urls import path

from asistencia import views


urlpatterns = [

    # ========================================================
    # ADMIN
    # ========================================================

    path(
        "admin/",
        admin.site.urls
    ),


    # ========================================================
    # PANTALLA DE ASISTENCIA
    # ========================================================

    path(
        "pantalla/",
        views.pantalla,
        name="pantalla_asistencia"
    ),


    # ========================================================
    # API RFID
    # ========================================================

    path(
        "api/asistencia/",
        views.registrar_rfid,
        name="registrar_rfid"
    ),


    # ========================================================
    # API CÉDULA
    # ========================================================

    path(
        "api/asistencia/cedula/",
        views.registrar_por_cedula,
        name="registrar_por_cedula"
    ),


    # ========================================================
    # ESTADO DE LA PANTALLA
    # ========================================================

    path(
        "api/estado/",
        views.estado_pantalla,
        name="estado_pantalla"
    ),


    # ========================================================
    # PRUEBA POR CÉDULA
    # ========================================================

    path(
        "prueba/<str:cedula>/",
        views.probar_asistencia,
        name="probar_asistencia"
    ),


    # ========================================================
    # REPORTES
    # ========================================================

    path(
        "reportes/",
        views.reportes_inicio,
        name="reportes_inicio"
    ),

    path(
        "reportes/fecha/",
        views.reporte_asistencia,
        name="reporte_asistencia"
    ),

    path(
        "reportes/mensual/",
        views.reporte_mensual_curso,
        name="reporte_mensual_curso"
    ),

    path(
        "reportes/mensual/excel/",
        views.exportar_reporte_mensual_excel,
        name="exportar_reporte_mensual_excel"
    ),

    path(
        "reportes/mensual/pdf/",
        views.exportar_reporte_mensual_pdf,
        name="exportar_reporte_mensual_pdf"
    ),

    path(
        "reportes/individual/",
        views.reporte_individual,
        name="reporte_individual"
    ),
]