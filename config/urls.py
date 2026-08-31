from django.contrib import admin
from django.urls import path

from asistencia import views


urlpatterns = [

    # ========================================================
    # ADMIN
    # ========================================================

    path(
        "admin/",
        admin.site.urls,
    ),


    # ========================================================
    # PANTALLA PRINCIPAL
    # ========================================================

    path(
        "pantalla/",
        views.pantalla,
        name="pantalla_asistencia",
    ),


    # ========================================================
    # API ASISTENCIA
    # ========================================================

    path(
        "api/asistencia/",
        views.registrar_rfid,
        name="registrar_rfid",
    ),

    path(
        "api/asistencia/cedula/",
        views.registrar_por_cedula,
        name="registrar_por_cedula",
    ),

    path(
        "api/estado/",
        views.estado_pantalla,
        name="estado_pantalla",
    ),


    # ========================================================
    # HORARIOS / CLASE
    # ========================================================

    path(
        "api/clase/estado/",
        views.estado_clase,
        name="estado_clase",
    ),

    path(
        "api/clase/iniciar/",
        views.iniciar_clase,
        name="iniciar_clase",
    ),

    path(
        "api/clase/finalizar/",
        views.finalizar_clase,
        name="finalizar_clase",
    ),


    # ========================================================
    # PRUEBA
    # ========================================================

    path(
        "prueba/<str:cedula>/",
        views.probar_asistencia,
        name="probar_asistencia",
    ),


    # ========================================================
    # REPORTES
    # ========================================================

    path(
        "reportes/",
        views.reportes_inicio,
        name="reportes_inicio",
    ),

    path(
        "reportes/fecha/",
        views.reporte_asistencia,
        name="reporte_asistencia",
    ),

    path(
        "reportes/mensual/",
        views.reporte_mensual_curso,
        name="reporte_mensual_curso",
    ),

    path(
        "reportes/individual/",
        views.reporte_individual,
        name="reporte_individual",
    ),
    
    path(
    "reportes/mensual/excel/",
    views.exportar_reporte_mensual_excel,
    name="exportar_reporte_mensual_excel",
),
    
    path(
    "reportes/mensual/pdf/",
    views.exportar_reporte_mensual_pdf,
    name="exportar_reporte_mensual_pdf",
),

]