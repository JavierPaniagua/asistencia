import calendar
from datetime import datetime, timedelta

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .models import Alumno, Asistencia
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

from io import BytesIO

from django.contrib.staticfiles import finders

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)

# ============================================================
# CONFIGURACIÓN
# ============================================================

# 4 horas = 240 minutos
MINUTOS_MINIMOS_SALIDA = 240


# ============================================================
# ÚLTIMO EVENTO MOSTRADO EN LA PANTALLA
# ============================================================

ultimo_evento = {
    "estado": "esperando",
    "nombre": "",
    "curso": "",
    "cedula": "",
    "fecha": "",
    "hora": "",
    "hora_entrada": "",
    "hora_salida": "",
    "mensaje": "Sistema listo para registrar asistencia",
    "evento_id": 0,
}


# Contador independiente para que cada lectura RFID
# tenga un evento diferente.
contador_eventos = 0


# ============================================================
# GENERAR ID DE EVENTO
# ============================================================

def nuevo_evento_id():
    global contador_eventos

    contador_eventos += 1

    return contador_eventos


# ============================================================
# ACTUALIZAR EVENTO
# ============================================================

def guardar_evento(evento):
    global ultimo_evento

    evento["evento_id"] = nuevo_evento_id()

    ultimo_evento = evento

    return evento


# ============================================================
# OBTENER NOMBRE DEL ALUMNO
# ============================================================

def obtener_nombre(alumno):

    try:
        if alumno.nombre:
            return alumno.nombre
    except Exception:
        pass

    return f"{alumno.apellidos}, {alumno.nombres}"


# ============================================================
# PANTALLA PRINCIPAL
# ============================================================

def pantalla(request):

    return render(
        request,
        "asistencia/pantalla.html"
    )


# ============================================================
# CONSULTAR ÚLTIMO EVENTO
# ============================================================

def estado_pantalla(request):

    return JsonResponse(
        ultimo_evento
    )


# ============================================================
# REGISTRAR ENTRADA / SALIDA
# ============================================================

def registrar_alumno(alumno):

    fecha_actual = timezone.localdate()

    ahora = timezone.localtime()

    hora_actual = ahora.time().replace(
        microsecond=0
    )

    # --------------------------------------------------------
    # Buscar asistencia del alumno para hoy
    # --------------------------------------------------------

    asistencia = (
        Asistencia.objects
        .filter(
            alumno=alumno,
            fecha=fecha_actual
        )
        .first()
    )

    # ========================================================
    # PRIMER REGISTRO = ENTRADA
    # ========================================================

    if asistencia is None:

        asistencia = Asistencia.objects.create(
            alumno=alumno,
            fecha=fecha_actual,
            hora_entrada=hora_actual
        )

        evento = {
            "estado": "entrada",
            "nombre": obtener_nombre(alumno),
            "curso": alumno.curso,
            "cedula": alumno.cedula,
            "fecha": fecha_actual.strftime("%d/%m/%Y"),
            "hora": hora_actual.strftime("%H:%M:%S"),
            "hora_entrada": hora_actual.strftime("%H:%M:%S"),
            "hora_salida": "",
            "mensaje": "Entrada registrada correctamente",
        }

        return guardar_evento(evento)

    # ========================================================
    # REGISTRO EXISTE PERO SIN HORA DE ENTRADA
    # ========================================================

    if asistencia.hora_entrada is None:

        asistencia.hora_entrada = hora_actual

        asistencia.save(
            update_fields=[
                "hora_entrada"
            ]
        )

        evento = {
            "estado": "entrada",
            "nombre": obtener_nombre(alumno),
            "curso": alumno.curso,
            "cedula": alumno.cedula,
            "fecha": fecha_actual.strftime("%d/%m/%Y"),
            "hora": hora_actual.strftime("%H:%M:%S"),
            "hora_entrada": hora_actual.strftime("%H:%M:%S"),
            "hora_salida": "",
            "mensaje": "Entrada registrada correctamente",
        }

        return guardar_evento(evento)

    # ========================================================
    # TIENE ENTRADA PERO NO TIENE SALIDA
    # ========================================================

    if (
        asistencia.hora_entrada
        and asistencia.hora_salida is None
    ):

        fecha_hora_entrada = datetime.combine(
            asistencia.fecha,
            asistencia.hora_entrada
        )

        # Convertimos a fecha/hora con zona horaria
        if timezone.is_naive(fecha_hora_entrada):

            fecha_hora_entrada = timezone.make_aware(
                fecha_hora_entrada,
                timezone.get_current_timezone()
            )

        diferencia = ahora - fecha_hora_entrada

        minutos_transcurridos = (
            diferencia.total_seconds() / 60
        )

        # ====================================================
        # TODAVÍA NO PASARON 4 HORAS
        # ====================================================

        if (
            minutos_transcurridos
            < MINUTOS_MINIMOS_SALIDA
        ):

            minutos_faltantes = max(
                0,
                int(
                    MINUTOS_MINIMOS_SALIDA
                    - minutos_transcurridos
                )
            )

            horas_faltantes = (
                minutos_faltantes // 60
            )

            minutos_restantes = (
                minutos_faltantes % 60
            )

            if (
                horas_faltantes > 0
                and minutos_restantes > 0
            ):

                tiempo_faltante = (
                    f"{horas_faltantes} h "
                    f"{minutos_restantes} min"
                )

            elif horas_faltantes > 0:

                tiempo_faltante = (
                    f"{horas_faltantes} h"
                )

            else:

                tiempo_faltante = (
                    f"{minutos_restantes} min"
                )

            evento = {
                "estado": "duplicado",
                "nombre": obtener_nombre(alumno),
                "curso": alumno.curso,
                "cedula": alumno.cedula,
                "fecha": fecha_actual.strftime("%d/%m/%Y"),
                "hora": hora_actual.strftime("%H:%M:%S"),

                "hora_entrada": (
                    asistencia.hora_entrada.strftime(
                        "%H:%M:%S"
                    )
                ),

                "hora_salida": "",

                "mensaje": (
                    "Entrada ya registrada. "
                    "La salida podrá registrarse "
                    f"dentro de {tiempo_faltante}."
                ),
            }

            return guardar_evento(evento)

        # ====================================================
        # YA PASARON 4 HORAS = SALIDA
        # ====================================================

        asistencia.hora_salida = hora_actual

        asistencia.save(
            update_fields=[
                "hora_salida"
            ]
        )

        evento = {
            "estado": "salida",
            "nombre": obtener_nombre(alumno),
            "curso": alumno.curso,
            "cedula": alumno.cedula,
            "fecha": fecha_actual.strftime("%d/%m/%Y"),
            "hora": hora_actual.strftime("%H:%M:%S"),

            "hora_entrada": (
                asistencia.hora_entrada.strftime(
                    "%H:%M:%S"
                )
            ),

            "hora_salida": (
                asistencia.hora_salida.strftime(
                    "%H:%M:%S"
                )
            ),

            "mensaje": "Salida registrada correctamente",
        }

        return guardar_evento(evento)

    # ========================================================
    # YA TIENE ENTRADA Y SALIDA
    # ========================================================

    if (
        asistencia.hora_entrada
        and asistencia.hora_salida
    ):

        evento = {
            "estado": "completo",
            "nombre": obtener_nombre(alumno),
            "curso": alumno.curso,
            "cedula": alumno.cedula,
            "fecha": fecha_actual.strftime("%d/%m/%Y"),
            "hora": hora_actual.strftime("%H:%M:%S"),

            "hora_entrada": (
                asistencia.hora_entrada.strftime(
                    "%H:%M:%S"
                )
            ),

            "hora_salida": (
                asistencia.hora_salida.strftime(
                    "%H:%M:%S"
                )
            ),

            "mensaje": (
                "El alumno ya registró entrada y salida"
            ),
        }

        return guardar_evento(evento)

    # ========================================================
    # ERROR INESPERADO
    # ========================================================

    evento = {
        "estado": "error",
        "nombre": obtener_nombre(alumno),
        "curso": alumno.curso,
        "cedula": alumno.cedula,
        "fecha": fecha_actual.strftime("%d/%m/%Y"),
        "hora": hora_actual.strftime("%H:%M:%S"),
        "hora_entrada": "",
        "hora_salida": "",
        "mensaje": (
            "No se pudo determinar "
            "el estado de asistencia"
        ),
    }

    return guardar_evento(evento)


# ============================================================
# REGISTRAR POR RFID
# ============================================================

def registrar_rfid(request):

    uid = request.GET.get(
        "uid",
        ""
    ).strip()

    # --------------------------------------------------------
    # UID vacío
    # --------------------------------------------------------

    if not uid:

        ahora = timezone.localtime()

        evento = {
            "estado": "error",
            "nombre": "",
            "curso": "",
            "cedula": "",
            "fecha": (
                timezone.localdate()
                .strftime("%d/%m/%Y")
            ),
            "hora": obtener_hora_texto(ahora),
            "hora_entrada": "",
            "hora_salida": "",
            "mensaje": "UID RFID no recibido",
        }

        return JsonResponse(
            guardar_evento(evento),
            status=400
        )

    # --------------------------------------------------------
    # Normalizar UID
    # --------------------------------------------------------

    uid = (
        uid
        .replace(" ", "")
        .replace(":", "")
        .replace("-", "")
        .upper()
    )

    # --------------------------------------------------------
    # Buscar alumno
    # --------------------------------------------------------

    alumno = (
        Alumno.objects
        .filter(
            uid_rfid__iexact=uid,
            activo=True
        )
        .first()
    )

    # --------------------------------------------------------
    # Tarjeta no registrada
    # --------------------------------------------------------

    if alumno is None:

        ahora = timezone.localtime()

        evento = {
            "estado": "desconocido",
            "nombre": "",
            "curso": "",
            "cedula": "",
            "fecha": (
                timezone.localdate()
                .strftime("%d/%m/%Y")
            ),
            "hora": obtener_hora_texto(ahora),
            "hora_entrada": "",
            "hora_salida": "",
            "mensaje": (
                "Tarjeta RFID no asignada "
                "a ningún alumno"
            ),
        }

        return JsonResponse(
            guardar_evento(evento)
        )

    # --------------------------------------------------------
    # Registrar
    # --------------------------------------------------------

    resultado = registrar_alumno(
        alumno
    )

    return JsonResponse(
        resultado
    )


# ============================================================
# FUNCIÓN AUXILIAR PARA HORA
# ============================================================

def obtener_hora_texto(ahora):

    return (
        ahora
        .time()
        .replace(
            microsecond=0
        )
        .strftime(
            "%H:%M:%S"
        )
    )


# ============================================================
# REGISTRAR POR CÉDULA
# ============================================================

def registrar_por_cedula(request):

    cedula = request.GET.get(
        "cedula",
        ""
    ).strip()

    # --------------------------------------------------------
    # Limpiar formato
    # --------------------------------------------------------

    cedula = (
        cedula
        .replace(".", "")
        .replace(" ", "")
        .replace("-", "")
    )

    # --------------------------------------------------------
    # Cédula vacía
    # --------------------------------------------------------

    if not cedula:

        evento = {
            "estado": "error",
            "nombre": "",
            "curso": "",
            "cedula": "",
            "fecha": (
                timezone.localdate()
                .strftime("%d/%m/%Y")
            ),
            "hora": (
                timezone.localtime()
                .strftime("%H:%M:%S")
            ),
            "hora_entrada": "",
            "hora_salida": "",
            "mensaje": (
                "Ingrese el número de cédula"
            ),
        }

        return JsonResponse(
            guardar_evento(evento),
            status=400
        )

    # --------------------------------------------------------
    # Buscar alumno
    # --------------------------------------------------------

    alumno = (
        Alumno.objects
        .filter(
            cedula=cedula,
            activo=True
        )
        .first()
    )

    if alumno is None:

        evento = {
            "estado": "desconocido",
            "nombre": "",
            "curso": "",
            "cedula": cedula,
            "fecha": (
                timezone.localdate()
                .strftime("%d/%m/%Y")
            ),
            "hora": (
                timezone.localtime()
                .strftime("%H:%M:%S")
            ),
            "hora_entrada": "",
            "hora_salida": "",
            "mensaje": (
                "No existe un alumno activo "
                "con esta cédula"
            ),
        }

        return JsonResponse(
            guardar_evento(evento)
        )

    # --------------------------------------------------------
    # Registrar
    # --------------------------------------------------------

    resultado = registrar_alumno(
        alumno
    )

    return JsonResponse(
        resultado
    )


# ============================================================
# PRUEBA POR URL
# ============================================================

def probar_asistencia(
    request,
    cedula
):

    alumno = (
        Alumno.objects
        .filter(
            cedula=cedula,
            activo=True
        )
        .first()
    )

    if alumno is None:

        return JsonResponse(
            {
                "estado": "desconocido",
                "mensaje": "Alumno no encontrado",
            },
            status=404
        )

    return JsonResponse(
        registrar_alumno(
            alumno
        )
    )


# ============================================================
# REPORTES
# ============================================================

def reportes_inicio(request):

    return render(
        request,
        "asistencia/reportes_inicio.html"
    )


# ============================================================
# REPORTE DIARIO
# ============================================================

def reporte_asistencia(request):

    fecha_texto = request.GET.get(
        "fecha",
        ""
    )

    curso = request.GET.get(
        "curso",
        ""
    ).strip()

    if fecha_texto:

        try:

            fecha_seleccionada = (
                datetime.strptime(
                    fecha_texto,
                    "%Y-%m-%d"
                ).date()
            )

        except ValueError:

            fecha_seleccionada = (
                timezone.localdate()
            )

    else:

        fecha_seleccionada = (
            timezone.localdate()
        )

    # --------------------------------------------------------
    # Cursos
    # --------------------------------------------------------

    cursos = (
        Alumno.objects
        .filter(
            activo=True
        )
        .exclude(
            curso=""
        )
        .values_list(
            "curso",
            flat=True
        )
        .distinct()
        .order_by(
            "curso"
        )
    )

    # --------------------------------------------------------
    # Alumnos
    # --------------------------------------------------------

    alumnos = (
        Alumno.objects
        .filter(
            activo=True
        )
        .order_by(
            "apellidos",
            "nombres"
        )
    )

    if curso:

        alumnos = alumnos.filter(
            curso=curso
        )

    # --------------------------------------------------------
    # Asistencias
    # --------------------------------------------------------

    asistencias = (
        Asistencia.objects
        .filter(
            fecha=fecha_seleccionada,
            alumno__in=alumnos
        )
        .select_related(
            "alumno"
        )
    )

    mapa = {
        registro.alumno_id: registro
        for registro in asistencias
    }

    filas = []

    presentes = 0
    completos = 0
    sin_salida = 0

    for alumno in alumnos:

        asistencia = mapa.get(
            alumno.id
        )

        if asistencia:

            presentes += 1

            if asistencia.hora_salida:

                estado = (
                    "JORNADA COMPLETA"
                )

                completos += 1

            else:

                estado = (
                    "EN EL COLEGIO"
                )

                sin_salida += 1

        else:

            estado = "AUSENTE"

        filas.append(
            {
                "alumno": alumno,
                "asistencia": asistencia,
                "estado": estado,
            }
        )

    total = len(filas)

    ausentes = (
        total - presentes
    )

    porcentaje = (
        round(
            presentes * 100 / total,
            1
        )
        if total
        else 0
    )

    contexto = {
        "fecha": fecha_seleccionada,
        "fecha_texto": (
            fecha_seleccionada.strftime(
                "%Y-%m-%d"
            )
        ),
        "curso": curso,
        "cursos": cursos,
        "filas": filas,
        "total": total,
        "presentes": presentes,
        "ausentes": ausentes,
        "completos": completos,
        "sin_salida": sin_salida,
        "porcentaje": porcentaje,
    }

    return render(
        request,
        "asistencia/reporte.html",
        contexto
    )


# ============================================================
# REPORTE MENSUAL
#
# Por ahora carga la plantilla.
# Después ajustaremos la planilla mensual completa
# al nuevo sistema entrada/salida.
# ============================================================

# ============================================================
# REPORTE MENSUAL POR CURSO
# ============================================================

# ============================================================
# REPORTE MENSUAL POR CURSO
# ============================================================

def reporte_mensual_curso(request):

    hoy = timezone.localdate()

    curso = request.GET.get("curso", "").strip()

    try:
        mes = int(request.GET.get("mes", hoy.month))
    except (TypeError, ValueError):
        mes = hoy.month

    try:
        anio = int(request.GET.get("anio", hoy.year))
    except (TypeError, ValueError):
        anio = hoy.year

    if mes < 1 or mes > 12:
        mes = hoy.month

    # ========================================================
    # CURSOS
    # ========================================================

    cursos = list(
        Alumno.objects
        .filter(activo=True)
        .exclude(curso="")
        .values_list("curso", flat=True)
        .distinct()
        .order_by("curso")
    )

    if not curso and cursos:
        curso = cursos[0]

    # ========================================================
    # ALUMNOS
    # ========================================================

    alumnos = (
        Alumno.objects
        .filter(
            activo=True,
            curso=curso
        )
        .order_by(
            "apellidos",
            "nombres"
        )
    )

    # ========================================================
    # MESES
    # ========================================================

    meses = [
        (1, "Enero"),
        (2, "Febrero"),
        (3, "Marzo"),
        (4, "Abril"),
        (5, "Mayo"),
        (6, "Junio"),
        (7, "Julio"),
        (8, "Agosto"),
        (9, "Septiembre"),
        (10, "Octubre"),
        (11, "Noviembre"),
        (12, "Diciembre"),
    ]

    nombres_meses = {
        1: "ENERO",
        2: "FEBRERO",
        3: "MARZO",
        4: "ABRIL",
        5: "MAYO",
        6: "JUNIO",
        7: "JULIO",
        8: "AGOSTO",
        9: "SEPTIEMBRE",
        10: "OCTUBRE",
        11: "NOVIEMBRE",
        12: "DICIEMBRE",
    }

    nombre_mes = nombres_meses[mes]

    # ========================================================
    # DÍAS HÁBILES
    # ========================================================

    ultimo_dia = calendar.monthrange(
        anio,
        mes
    )[1]

    dias = []

    nombres_dias = {
        0: "L",
        1: "M",
        2: "X",
        3: "J",
        4: "V",
    }

    for numero_dia in range(
        1,
        ultimo_dia + 1
    ):

        fecha = datetime(
            anio,
            mes,
            numero_dia
        ).date()

        if fecha.weekday() <= 4:

            dias.append(
                {
                    "fecha": fecha,
                    "numero": numero_dia,
                    "dia_semana": nombres_dias[
                        fecha.weekday()
                    ],
                }
            )

    # ========================================================
    # ASISTENCIAS
    # ========================================================

    asistencias = (
        Asistencia.objects
        .filter(
            alumno__in=alumnos,
            fecha__year=anio,
            fecha__month=mes
        )
        .select_related("alumno")
    )

    mapa_asistencias = {}

    for asistencia in asistencias:

        mapa_asistencias[
            (
                asistencia.alumno_id,
                asistencia.fecha
            )
        ] = asistencia

    # ========================================================
    # FILAS
    # ========================================================

    filas = []

    for numero, alumno in enumerate(
        alumnos,
        start=1
    ):

        celdas = []

        jornadas_completas = 0
        solo_entrada = 0
        presentes = 0
        ausentes = 0

        for dia in dias:

            fecha = dia["fecha"]

            asistencia = mapa_asistencias.get(
                (
                    alumno.id,
                    fecha
                )
            )

            # FECHA FUTURA

            if fecha > hoy:

                estado = "PENDIENTE"
                texto = "-"

            # PRESENTE

            elif (
                asistencia
                and asistencia.hora_entrada
            ):

                presentes += 1

                if asistencia.hora_salida:

                    estado = "COMPLETO"
                    texto = "C"
                    jornadas_completas += 1

                else:

                    estado = "PRESENTE"
                    texto = "E"
                    solo_entrada += 1

            # AUSENTE

            else:

                ausentes += 1

                estado = "AUSENTE"
                texto = "A"

            celdas.append(
                {
                    "fecha": fecha,
                    "estado": estado,
                    "texto": texto,
                    "asistencia": asistencia,
                }
            )

        dias_computados = (
            presentes + ausentes
        )

        if dias_computados > 0:

            porcentaje = round(
                presentes
                * 100
                / dias_computados,
                1
            )

        else:

            porcentaje = 0

        filas.append(
            {
                "numero": numero,
                "alumno": alumno,
                "celdas": celdas,
                "jornadas_completas": jornadas_completas,
                "solo_entrada": solo_entrada,
                "presentes": presentes,
                "ausentes": ausentes,
                "porcentaje": porcentaje,
            }
        )

    contexto = {

        "curso": curso,
        "cursos": cursos,

        "mes": mes,
        "meses": meses,

        "anio": anio,

        "nombre_mes": nombre_mes,

        "dias": dias,

        "filas": filas,

        "total_alumnos": alumnos.count(),

    }

    return render(
        request,
        "asistencia/reporte_mensual_curso.html",
        contexto
    )


# ============================================================
# EXPORTAR REPORTE MENSUAL A EXCEL
# ============================================================

def exportar_reporte_mensual_excel(request):

    hoy = timezone.localdate()

    curso = request.GET.get(
        "curso",
        ""
    ).strip()

    try:
        mes = int(
            request.GET.get(
                "mes",
                hoy.month
            )
        )
    except (TypeError, ValueError):
        mes = hoy.month

    try:
        anio = int(
            request.GET.get(
                "anio",
                hoy.year
            )
        )
    except (TypeError, ValueError):
        anio = hoy.year

    if mes < 1 or mes > 12:
        mes = hoy.month

    # ========================================================
    # ALUMNOS
    # ========================================================

    alumnos = (
        Alumno.objects
        .filter(
            activo=True,
            curso=curso
        )
        .order_by(
            "apellidos",
            "nombres"
        )
    )

    # ========================================================
    # MES
    # ========================================================

    nombres_meses = {
        1: "ENERO",
        2: "FEBRERO",
        3: "MARZO",
        4: "ABRIL",
        5: "MAYO",
        6: "JUNIO",
        7: "JULIO",
        8: "AGOSTO",
        9: "SEPTIEMBRE",
        10: "OCTUBRE",
        11: "NOVIEMBRE",
        12: "DICIEMBRE",
    }

    nombre_mes = nombres_meses[mes]

    # ========================================================
    # DÍAS HÁBILES
    # ========================================================

    ultimo_dia = calendar.monthrange(
        anio,
        mes
    )[1]

    dias = []

    nombres_dias = {
        0: "L",
        1: "M",
        2: "X",
        3: "J",
        4: "V",
    }

    for numero_dia in range(
        1,
        ultimo_dia + 1
    ):

        fecha = datetime(
            anio,
            mes,
            numero_dia
        ).date()

        if fecha.weekday() <= 4:

            dias.append(
                {
                    "fecha": fecha,
                    "numero": numero_dia,
                    "dia_semana": nombres_dias[
                        fecha.weekday()
                    ],
                }
            )

    # ========================================================
    # ASISTENCIAS
    # ========================================================

    asistencias = (
        Asistencia.objects
        .filter(
            alumno__in=alumnos,
            fecha__year=anio,
            fecha__month=mes
        )
        .select_related("alumno")
    )

    mapa_asistencias = {}

    for asistencia in asistencias:

        mapa_asistencias[
            (
                asistencia.alumno_id,
                asistencia.fecha
            )
        ] = asistencia

    # ========================================================
    # CREAR EXCEL
    # ========================================================

    wb = Workbook()

    ws = wb.active

    ws.title = "Asistencia mensual"

    # ========================================================
    # HOJA OFICIO HORIZONTAL
    # ========================================================

    ws.page_setup.orientation = "landscape"

    ws.page_setup.paperSize = ws.PAPERSIZE_FOLIO

    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1

    ws.sheet_properties.pageSetUpPr.fitToPage = True

    ws.page_margins.left = 0.15
    ws.page_margins.right = 0.15
    ws.page_margins.top = 0.20
    ws.page_margins.bottom = 0.20

    # ========================================================
    # ESTILOS
    # ========================================================

    lado = Side(
        style="thin",
        color="000000"
    )

    borde = Border(
        left=lado,
        right=lado,
        top=lado,
        bottom=lado
    )

    relleno_encabezado = PatternFill(
        fill_type="solid",
        fgColor="D9EAF7"
    )

    relleno_presente = PatternFill(
        fill_type="solid",
        fgColor="D1E7DD"
    )

    relleno_ausente = PatternFill(
        fill_type="solid",
        fgColor="F8D7DA"
    )

    relleno_pendiente = PatternFill(
        fill_type="solid",
        fgColor="FFF3CD"
    )

    # ========================================================
    # TOTAL COLUMNAS
    # ========================================================

    total_columnas = (
        3
        + len(dias)
        + 3
    )

    ultima_columna = get_column_letter(
        total_columnas
    )

    # ========================================================
    # ENCABEZADO CENTRADO
    # ========================================================

    ws.merge_cells(
        f"A1:{ultima_columna}1"
    )

    ws["A1"] = "COLEGIO NACIONAL"

    ws["A1"].font = Font(
        bold=True,
        size=14
    )

    ws["A1"].alignment = Alignment(
        horizontal="center"
    )

    ws.merge_cells(
        f"A2:{ultima_columna}2"
    )

    ws["A2"] = (
        "GRAL. JOSÉ ELIZARDO AQUINO - LUQUE"
    )

    ws["A2"].font = Font(
        bold=True,
        size=12
    )

    ws["A2"].alignment = Alignment(
        horizontal="center"
    )

    ws.merge_cells(
        f"A3:{ultima_columna}3"
    )

    ws["A3"] = (
        "PLANILLA MENSUAL DE ASISTENCIA"
    )

    ws["A3"].font = Font(
        bold=True,
        size=14
    )

    ws["A3"].alignment = Alignment(
        horizontal="center"
    )

    # ========================================================
    # DATOS
    # ========================================================

    ws["A5"] = "CURSO:"
    ws["B5"] = curso

    ws["D5"] = "MES:"
    ws["E5"] = nombre_mes

    ws["G5"] = "AÑO:"
    ws["H5"] = anio

    ws["A5"].font = Font(bold=True)
    ws["D5"].font = Font(bold=True)
    ws["G5"].font = Font(bold=True)

    # ========================================================
    # ENCABEZADOS
    # ========================================================

    fila_encabezado = 7

    ws.cell(
        row=fila_encabezado,
        column=1,
        value="N°"
    )

    ws.cell(
        row=fila_encabezado,
        column=2,
        value="C.I."
    )

    ws.cell(
        row=fila_encabezado,
        column=3,
        value="ALUMNO"
    )

    columna = 4

    for dia in dias:

        ws.cell(
            row=fila_encabezado,
            column=columna,
            value=(
                f"{dia['numero']}\n"
                f"{dia['dia_semana']}"
            )
        )

        columna += 1

    columna_presentes = columna
    columna_ausentes = columna + 1
    columna_porcentaje = columna + 2

    ws.cell(
        row=fila_encabezado,
        column=columna_presentes,
        value="P"
    )

    ws.cell(
        row=fila_encabezado,
        column=columna_ausentes,
        value="A"
    )

    ws.cell(
        row=fila_encabezado,
        column=columna_porcentaje,
        value="%"
    )

    for c in range(
        1,
        total_columnas + 1
    ):

        celda = ws.cell(
            row=fila_encabezado,
            column=c
        )

        celda.font = Font(
            bold=True,
            size=6.5
        )

        celda.fill = relleno_encabezado

        celda.border = borde

        celda.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
            shrink_to_fit=True
        )

    # ========================================================
    # ALUMNOS
    # ========================================================

    fila_excel = 8

    for numero, alumno in enumerate(
        alumnos,
        start=1
    ):

        presentes = 0
        ausentes = 0

        ws.cell(
            row=fila_excel,
            column=1,
            value=numero
        )

        ws.cell(
            row=fila_excel,
            column=2,
            value=alumno.cedula
        )

        ws.cell(
            row=fila_excel,
            column=3,
            value=(
                f"{alumno.apellidos}, "
                f"{alumno.nombres}"
            )
        )

        columna_dia = 4

        for dia in dias:

            fecha = dia["fecha"]

            asistencia = mapa_asistencias.get(
                (
                    alumno.id,
                    fecha
                )
            )

            celda = ws.cell(
                row=fila_excel,
                column=columna_dia
            )

            if fecha > hoy:

                celda.value = "-"
                celda.fill = relleno_pendiente

            elif (
                asistencia
                and asistencia.hora_entrada
            ):

                celda.value = "P"
                celda.fill = relleno_presente

                presentes += 1

            else:

                celda.value = "A"
                celda.fill = relleno_ausente

                ausentes += 1

            columna_dia += 1

        dias_computados = (
            presentes
            + ausentes
        )

        if dias_computados > 0:

            porcentaje = round(
                presentes
                * 100
                / dias_computados,
                1
            )

        else:

            porcentaje = 0

        ws.cell(
            row=fila_excel,
            column=columna_presentes,
            value=presentes
        )

        ws.cell(
            row=fila_excel,
            column=columna_ausentes,
            value=ausentes
        )

        ws.cell(
            row=fila_excel,
            column=columna_porcentaje,
            value=f"{porcentaje}%"
        )

        for c in range(
            1,
            total_columnas + 1
        ):

            celda = ws.cell(
                row=fila_excel,
                column=c
            )

            celda.border = borde

            if c == 3:
                # Nombre completo: mantenerlo en una sola línea y
                # reducir automáticamente la fuente solo si hace falta.
                celda.font = Font(size=7)
                celda.alignment = Alignment(
                    horizontal="left",
                    vertical="center",
                    wrap_text=False,
                    shrink_to_fit=True
                )
            else:
                celda.font = Font(size=6.5)
                celda.alignment = Alignment(
                    horizontal="center",
                    vertical="center",
                    wrap_text=False,
                    shrink_to_fit=True
                )

        fila_excel += 1

    # ========================================================
    # TAMAÑO COLUMNAS - AJUSTADO PARA OFICIO HORIZONTAL
    # Prioridad: ALUMNO amplio; C.I., días y totales compactos.
    # ========================================================

    # N°
    ws.column_dimensions["A"].width = 2.5

    # C.I.
    ws.column_dimensions["B"].width = 7.0

    # ALUMNO: espacio principal para apellido y nombre completos
    ws.column_dimensions["C"].width = 55

    # DÍAS: solo contienen P / A / -
    for numero_columna in range(
        4,
        4 + len(dias)
    ):

        letra = get_column_letter(
            numero_columna
        )

        ws.column_dimensions[
            letra
        ].width = 2.15

    # P / A / %
    for numero_columna in range(
        columna_presentes,
        columna_porcentaje + 1
    ):

        letra = get_column_letter(
            numero_columna
        )

        ws.column_dimensions[
            letra
        ].width = 3.6

    # ========================================================
    # ALTURAS
    # ========================================================

    ws.row_dimensions[1].height = 20
    ws.row_dimensions[2].height = 18
    ws.row_dimensions[3].height = 22
    ws.row_dimensions[7].height = 22

    for fila in range(8, fila_excel):
        ws.row_dimensions[fila].height = 14

    # ========================================================
    # CONGELAR
    # ========================================================

    ws.freeze_panes = "D8"

    # ========================================================
    # ÁREA DE IMPRESIÓN
    # ========================================================

    ultima_fila = fila_excel - 1

    ws.print_area = (
        f"A1:"
        f"{ultima_columna}"
        f"{ultima_fila}"
    )

    # ========================================================
    # RESPUESTA
    # ========================================================

    response = HttpResponse(
        content_type=(
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )

    curso_archivo = (
        curso
        .replace(" ", "_")
        .replace("°", "")
    )

    nombre_archivo = (
        f"asistencia_"
        f"{curso_archivo}_"
        f"{mes:02d}_"
        f"{anio}.xlsx"
    )

    response[
        "Content-Disposition"
    ] = (
        f'attachment; '
        f'filename="{nombre_archivo}"'
    )

    wb.save(response)

    return response

# ============================================================
# REPORTE INDIVIDUAL POR ALUMNO
# ============================================================

def reporte_individual(request):

    hoy = timezone.localdate()

    alumnos = (
        Alumno.objects
        .filter(activo=True)
        .order_by(
            "apellidos",
            "nombres"
        )
    )

    alumno_id = request.GET.get(
        "alumno",
        ""
    ).strip()

    fecha_desde_texto = request.GET.get(
        "fecha_desde",
        ""
    ).strip()

    fecha_hasta_texto = request.GET.get(
        "fecha_hasta",
        ""
    ).strip()

    fecha_desde = hoy.replace(day=1)
    fecha_hasta = hoy

    if fecha_desde_texto:
        try:
            fecha_desde = datetime.strptime(
                fecha_desde_texto,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            pass

    if fecha_hasta_texto:
        try:
            fecha_hasta = datetime.strptime(
                fecha_hasta_texto,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            pass

    if fecha_desde > fecha_hasta:
        fecha_desde, fecha_hasta = (
            fecha_hasta,
            fecha_desde
        )

    alumno_seleccionado = None
    filas = []
    presentes = 0
    ausentes = 0
    completos = 0
    en_colegio = 0

    if alumno_id:
        try:
            alumno_seleccionado = (
                Alumno.objects
                .filter(
                    id=int(alumno_id),
                    activo=True
                )
                .first()
            )
        except (TypeError, ValueError):
            alumno_seleccionado = None

    if alumno_seleccionado:
        asistencias = (
            Asistencia.objects
            .filter(
                alumno=alumno_seleccionado,
                fecha__range=(
                    fecha_desde,
                    fecha_hasta
                )
            )
            .order_by("fecha")
        )

        mapa_asistencias = {
            asistencia.fecha: asistencia
            for asistencia in asistencias
        }

        fecha_actual = fecha_desde

        nombres_dias = {
            0: "Lunes",
            1: "Martes",
            2: "Miércoles",
            3: "Jueves",
            4: "Viernes",
        }

        while fecha_actual <= fecha_hasta:
            if fecha_actual.weekday() <= 4:
                asistencia = mapa_asistencias.get(fecha_actual)

                if fecha_actual > hoy:
                    estado = "PENDIENTE"
                elif asistencia and asistencia.hora_entrada:
                    presentes += 1
                    if asistencia.hora_salida:
                        estado = "JORNADA COMPLETA"
                        completos += 1
                    else:
                        estado = "EN EL COLEGIO"
                        en_colegio += 1
                else:
                    estado = "AUSENTE"
                    ausentes += 1

                filas.append(
                    {
                        "fecha": fecha_actual,
                        "dia": nombres_dias[fecha_actual.weekday()],
                        "asistencia": asistencia,
                        "estado": estado,
                    }
                )

            fecha_actual += timedelta(days=1)

    dias_computados = presentes + ausentes

    if dias_computados:
        porcentaje = round(
            presentes * 100 / dias_computados,
            1
        )
    else:
        porcentaje = 0

    contexto = {
        "alumnos": alumnos,
        "alumno_seleccionado": alumno_seleccionado,
        "alumno_id": alumno_id,
        "fecha_desde": fecha_desde.strftime("%Y-%m-%d"),
        "fecha_hasta": fecha_hasta.strftime("%Y-%m-%d"),
        "filas": filas,
        "dias_computados": dias_computados,
        "presentes": presentes,
        "ausentes": ausentes,
        "completos": completos,
        "en_colegio": en_colegio,
        "porcentaje": porcentaje,
    }

    return render(
        request,
        "asistencia/reporte_individual.html",
        contexto
    )


# ============================================================
# EXPORTAR REPORTE MENSUAL A PDF
# ============================================================

def exportar_reporte_mensual_pdf(request):
    """Exporta la planilla mensual adaptada al sistema de entrada/salida.

    C = Jornada completa (entrada + salida)
    E = Solo entrada
    A = Ausente
    - = Fecha futura / pendiente
    """

    hoy = timezone.localdate()
    curso = request.GET.get("curso", "").strip()

    try:
        mes = int(request.GET.get("mes", hoy.month))
    except (TypeError, ValueError):
        mes = hoy.month

    try:
        anio = int(request.GET.get("anio", hoy.year))
    except (TypeError, ValueError):
        anio = hoy.year

    if mes < 1 or mes > 12:
        mes = hoy.month

    cursos = list(
        Alumno.objects
        .filter(activo=True)
        .exclude(curso="")
        .values_list("curso", flat=True)
        .distinct()
        .order_by("curso")
    )

    if not curso and cursos:
        curso = cursos[0]

    alumnos = list(
        Alumno.objects
        .filter(activo=True, curso=curso)
        .order_by("apellidos", "nombres")
    )

    nombres_meses = {
        1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL",
        5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO",
        9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE",
    }
    nombre_mes = nombres_meses[mes]

    # Solo días hábiles de lunes a viernes.
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    nombres_dias = {0: "L", 1: "M", 2: "X", 3: "J", 4: "V"}
    dias = []

    for numero_dia in range(1, ultimo_dia + 1):
        fecha = datetime(anio, mes, numero_dia).date()
        if fecha.weekday() <= 4:
            dias.append({
                "fecha": fecha,
                "numero": numero_dia,
                "dia_semana": nombres_dias[fecha.weekday()],
            })

    asistencias = (
        Asistencia.objects
        .filter(
            alumno__in=alumnos,
            fecha__year=anio,
            fecha__month=mes,
        )
        .select_related("alumno")
    )

    mapa_asistencias = {
        (a.alumno_id, a.fecha): a
        for a in asistencias
    }

    buffer = BytesIO()
    pagina_oficio_horizontal = (13 * inch, 8.5 * inch)

    documento = SimpleDocTemplate(
        buffer,
        pagesize=pagina_oficio_horizontal,
        rightMargin=9,
        leftMargin=9,
        topMargin=7,
        bottomMargin=7,
        title="Planilla mensual de entrada y salida",
        author="Sistema de Asistencia",
    )

    elementos = []

    estilo_colegio = ParagraphStyle(
        "ColegioPDF", fontName="Helvetica-Bold", fontSize=8.5,
        leading=9.2, alignment=TA_CENTER, spaceAfter=0, spaceBefore=0,
    )
    estilo_subtitulo = ParagraphStyle(
        "SubtituloPDF", fontName="Helvetica", fontSize=7.2,
        leading=8, alignment=TA_CENTER, spaceAfter=0, spaceBefore=0,
    )
    estilo_titulo = ParagraphStyle(
        "TituloPDF", fontName="Helvetica-Bold", fontSize=10,
        leading=10.5, alignment=TA_CENTER, spaceAfter=0, spaceBefore=0,
    )
    estilo_nombre = ParagraphStyle(
        "NombreAlumnoPDF", fontName="Helvetica-Bold", fontSize=7.0,
        leading=7.3, alignment=0, spaceAfter=0, spaceBefore=0,
    )
    estilo_dato = ParagraphStyle(
        "DatoPDF", fontName="Helvetica", fontSize=7.2, leading=7.8,
    )
    estilo_leyenda = ParagraphStyle(
        "LeyendaPDF", fontName="Helvetica", fontSize=6.8,
        leading=7.4, alignment=TA_CENTER,
    )

    ruta_logo = finders.find("asistencia/img/logo_colegio.png")
    if ruta_logo:
        logo = Image(ruta_logo, width=32, height=32)
        logo.hAlign = "CENTER"
        elementos.append(logo)

    elementos.append(Paragraph("COLEGIO NACIONAL", estilo_colegio))
    elementos.append(Paragraph("GRAL. JOSÉ ELIZARDO AQUINO - LUQUE", estilo_subtitulo))
    elementos.append(Paragraph("PLANILLA MENSUAL DE ENTRADA Y SALIDA", estilo_titulo))
    elementos.append(Spacer(1, 3))

    tabla_datos = Table(
        [[
            Paragraph(f"<b>CURSO:</b> {curso}", estilo_dato),
            Paragraph(f"<b>MES:</b> {nombre_mes}", estilo_dato),
            Paragraph(f"<b>AÑO:</b> {anio}", estilo_dato),
            Paragraph(f"<b>TOTAL ALUMNOS:</b> {len(alumnos)}", estilo_dato),
        ]],
        colWidths=[125, 125, 100, 160],
        hAlign="LEFT",
    )
    tabla_datos.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    elementos.append(tabla_datos)
    elementos.append(Spacer(1, 2))

    encabezado = ["N°", "C.I.", "ALUMNO"]
    for dia in dias:
        encabezado.append(f"{dia['numero']}\n{dia['dia_semana']}")
    encabezado.extend(["JC", "SE", "A", "%"])

    datos_tabla = [encabezado]

    for numero, alumno in enumerate(alumnos, start=1):
        jornadas_completas = 0
        solo_entrada = 0
        ausentes = 0
        presentes = 0

        nombre_completo = f"{alumno.apellidos}, {alumno.nombres}"
        fila = [
            str(numero),
            str(alumno.cedula),
            Paragraph(nombre_completo, estilo_nombre),
        ]

        for dia in dias:
            fecha = dia["fecha"]
            asistencia = mapa_asistencias.get((alumno.id, fecha))

            if fecha > hoy:
                fila.append("-")
            elif asistencia and asistencia.hora_entrada:
                presentes += 1
                if asistencia.hora_salida:
                    fila.append("C")
                    jornadas_completas += 1
                else:
                    fila.append("E")
                    solo_entrada += 1
            else:
                fila.append("A")
                ausentes += 1

        dias_computados = presentes + ausentes
        porcentaje = round(presentes * 100 / dias_computados, 1) if dias_computados else 0

        fila.extend([
            str(jornadas_completas),
            str(solo_entrada),
            str(ausentes),
            f"{porcentaje}%",
        ])
        datos_tabla.append(fila)

    # Anchos optimizados para Oficio horizontal.
    ancho_numero = 16
    ancho_cedula = 41
    ancho_alumno = 218
    ancho_jc = 22
    ancho_se = 22
    ancho_a = 20
    ancho_porcentaje = 32

    cantidad_dias = len(dias)
    ancho_pagina_util = (
        pagina_oficio_horizontal[0]
        - documento.leftMargin
        - documento.rightMargin
    )
    ancho_fijo = (
        ancho_numero + ancho_cedula + ancho_alumno
        + ancho_jc + ancho_se + ancho_a + ancho_porcentaje
    )
    ancho_dia = ((ancho_pagina_util - ancho_fijo) / cantidad_dias) if cantidad_dias else 20
    ancho_dia = max(12.5, min(ancho_dia, 23))

    anchos_columnas = [ancho_numero, ancho_cedula, ancho_alumno]
    anchos_columnas.extend([ancho_dia for _ in dias])
    anchos_columnas.extend([ancho_jc, ancho_se, ancho_a, ancho_porcentaje])

    tabla = Table(
        datos_tabla,
        colWidths=anchos_columnas,
        repeatRows=1,
        hAlign="CENTER",
    )

    estilo_tabla = [
        ("GRID", (0, 0), (-1, -1), 0.45, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E9ECEF")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 6.5),
        ("FONTSIZE", (0, 1), (-1, -1), 6.8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (2, 1), (2, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.1),
        ("TOPPADDING", (0, 0), (-1, -1), 1.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.4),
    ]

    columna_inicio_dias = 3
    for fila_indice, alumno in enumerate(alumnos, start=1):
        for indice_dia, dia in enumerate(dias):
            fecha = dia["fecha"]
            asistencia = mapa_asistencias.get((alumno.id, fecha))
            columna = columna_inicio_dias + indice_dia

            if fecha > hoy:
                color_fondo = colors.HexColor("#FFF3CD")       # pendiente
            elif asistencia and asistencia.hora_entrada and asistencia.hora_salida:
                color_fondo = colors.HexColor("#D1E7DD")       # completa
            elif asistencia and asistencia.hora_entrada:
                color_fondo = colors.HexColor("#DDEBFF")       # solo entrada
            else:
                color_fondo = colors.HexColor("#F8D7DA")       # ausente

            estilo_tabla.append((
                "BACKGROUND",
                (columna, fila_indice),
                (columna, fila_indice),
                color_fondo,
            ))

    tabla.setStyle(TableStyle(estilo_tabla))
    elementos.append(tabla)
    elementos.append(Spacer(1, 3))
    elementos.append(Paragraph(
        "<b>Leyenda:</b> C = Jornada completa (entrada y salida) &nbsp;&nbsp; "
        "E = Solo entrada &nbsp;&nbsp; A = Ausente &nbsp;&nbsp; - = Fecha pendiente &nbsp;&nbsp; "
        "JC = Jornadas completas &nbsp;&nbsp; SE = Solo entrada",
        estilo_leyenda,
    ))

    documento.build(elementos)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type="application/pdf")
    curso_archivo = curso.replace(" ", "_").replace("°", "")
    nombre_archivo = f"entrada_salida_{curso_archivo}_{mes:02d}_{anio}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
    return response

