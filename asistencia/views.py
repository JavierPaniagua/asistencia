import calendar
from datetime import datetime, timedelta

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .models import Alumno, Asistencia
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

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
            "hora": agora_hora(ahora),
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
            "hora": agora_hora(ahora),
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

    return (
        agora
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

                else:

                    estado = "PRESENTE"

                texto = "P"

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

    ws.page_margins.left = 0.25
    ws.page_margins.right = 0.25
    ws.page_margins.top = 0.25
    ws.page_margins.bottom = 0.25

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
            size=8
        )

        celda.fill = relleno_encabezado

        celda.border = borde

        celda.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True
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

            celda.font = Font(
                size=7
            )

            celda.alignment = Alignment(
                horizontal=(
                    "left"
                    if c == 3
                    else "center"
                ),
                vertical="center"
            )

        fila_excel += 1

    # ========================================================
    # TAMAÑO COLUMNAS
    # ========================================================

    ws.column_dimensions["A"].width = 4
    ws.column_dimensions["B"].width = 10
    ws.column_dimensions["C"].width = 32

    for numero_columna in range(
        4,
        4 + len(dias)
    ):

        letra = get_column_letter(
            numero_columna
        )

        ws.column_dimensions[
            letra
        ].width = 3.5

    for numero_columna in range(
        columna_presentes,
        columna_porcentaje + 1
    ):

        letra = get_column_letter(
            numero_columna
        )

        ws.column_dimensions[
            letra
        ].width = 6

    # ========================================================
    # ALTURAS
    # ========================================================

    ws.row_dimensions[1].height = 20
    ws.row_dimensions[2].height = 18
    ws.row_dimensions[3].height = 22
    ws.row_dimensions[7].height = 25

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

    hoy = timezone.localdate()

    # --------------------------------------------------------
    # OBTENER PARÁMETROS
    # --------------------------------------------------------

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


    # Validar mes

    if mes < 1 or mes > 12:
        mes = hoy.month


    # --------------------------------------------------------
    # CURSOS DISPONIBLES
    # --------------------------------------------------------

    cursos = list(
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


    # Si no se seleccionó curso, tomar el primero

    if not curso and cursos:
        curso = cursos[0]


    # --------------------------------------------------------
    # ALUMNOS DEL CURSO
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # NOMBRE DEL MES
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # DÍAS HÁBILES DEL MES
    # Lunes a viernes
    # --------------------------------------------------------

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


        # 0 = lunes
        # 4 = viernes
        # 5 = sábado
        # 6 = domingo

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


    # --------------------------------------------------------
    # ASISTENCIAS DEL MES
    # --------------------------------------------------------

    asistencias = (
        Asistencia.objects
        .filter(
            alumno__in=alumnos,
            fecha__year=anio,
            fecha__month=mes
        )
        .select_related(
            "alumno"
        )
    )


    mapa_asistencias = {}


    for asistencia in asistencias:

        clave = (
            asistencia.alumno_id,
            asistencia.fecha
        )

        mapa_asistencias[clave] = asistencia


    # --------------------------------------------------------
    # CONSTRUIR FILAS
    # --------------------------------------------------------

    filas = []


    for numero, alumno in enumerate(
        alumnos,
        start=1
    ):

        celdas = []

        presentes = 0
        ausentes = 0
        completos = 0


        for dia in dias:

            fecha = dia["fecha"]

            asistencia = mapa_asistencias.get(
                (
                    alumno.id,
                    fecha
                )
            )


            # ------------------------------------------------
            # FECHA FUTURA
            # ------------------------------------------------

            if fecha > hoy:

                estado = "PENDIENTE"

                texto = "-"


            # ------------------------------------------------
            # PRESENTE
            # ------------------------------------------------

            elif (
                asistencia
                and asistencia.hora_entrada
            ):

                presentes += 1

                if asistencia.hora_salida:

                    completos += 1

                    estado = "COMPLETO"

                    texto = "P"

                else:

                    estado = "PRESENTE"

                    texto = "P"


            # ------------------------------------------------
            # AUSENTE
            # ------------------------------------------------

            else:

                estado = "AUSENTE"

                texto = "A"

                ausentes += 1


            celdas.append(
                {
                    "fecha": fecha,
                    "estado": estado,
                    "texto": texto,
                    "asistencia": asistencia,
                }
            )


        # ----------------------------------------------------
        # PORCENTAJE
        # ----------------------------------------------------

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


        filas.append(
            {
                "numero": numero,
                "alumno": alumno,
                "celdas": celdas,
                "presentes": presentes,
                "ausentes": ausentes,
                "completos": completos,
                "porcentaje": porcentaje,
            }
        )


    # --------------------------------------------------------
    # CONTEXTO
    # --------------------------------------------------------

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

    return render(
        request,
        "asistencia/reporte_mensual_curso.html",
        {
            "alumnos": (
                Alumno.objects
                .filter(
                    activo=True
                )
                .order_by(
                    "apellidos",
                    "nombres"
                )
            )
        }
    )


# ============================================================
# REPORTE INDIVIDUAL
# ============================================================

def reporte_individual(request):

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

    return render(
        request,
        "asistencia/reporte_individual.html",
        {
            "alumnos": alumnos
        }
    )


# ============================================================
# EXPORTAR EXCEL
#
# Se deja temporalmente disponible para que Django
# encuentre la función. Luego adaptaremos el Excel definitivo.
# ============================================================

def exportar_reporte_mensual_excel(request):

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


    # ==========================================================
    # ALUMNOS
    # ==========================================================

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


    # ==========================================================
    # NOMBRE DEL MES
    # ==========================================================

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


    # ==========================================================
    # DÍAS HÁBILES
    # ==========================================================

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

    for numero_dia in range(1, ultimo_dia + 1):

        fecha = datetime(
            anio,
            mes,
            numero_dia
        ).date()

        if fecha.weekday() <= 4:

            dias.append({
                "fecha": fecha,
                "numero": numero_dia,
                "dia_semana": nombres_dias[
                    fecha.weekday()
                ],
            })


    # ==========================================================
    # ASISTENCIAS
    # ==========================================================

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


    # ==========================================================
    # CREAR EXCEL
    # ==========================================================

    wb = Workbook()

    ws = wb.active

    ws.title = "Asistencia mensual"


    # ==========================================================
    # CONFIGURACIÓN DE IMPRESIÓN
    # OFICIO HORIZONTAL
    # ==========================================================

    ws.page_setup.orientation = "landscape"

    ws.page_setup.paperSize = ws.PAPERSIZE_FOLIO

    ws.page_setup.fitToWidth = 1

    ws.page_setup.fitToHeight = 1

    ws.sheet_properties.pageSetUpPr.fitToPage = True

    ws.page_margins.left = 0.25
    ws.page_margins.right = 0.25
    ws.page_margins.top = 0.25
    ws.page_margins.bottom = 0.25
    ws.page_margins.header = 0.1
    ws.page_margins.footer = 0.1


    # ==========================================================
    # ESTILOS
    # ==========================================================

    borde_fino = Side(
        style="thin",
        color="000000"
    )

    borde = Border(
        left=borde_fino,
        right=borde_fino,
        top=borde_fino,
        bottom=borde_fino
    )


    encabezado_fill = PatternFill(
        "solid",
        fgColor="D9EAF7"
    )


    presente_fill = PatternFill(
        "solid",
        fgColor="D1E7DD"
    )


    ausente_fill = PatternFill(
        "solid",
        fgColor="F8D7DA"
    )


    pendiente_fill = PatternFill(
        "solid",
        fgColor="FFF3CD"
    )


    # ==========================================================
    # TÍTULO
    # ==========================================================

    total_columnas = (
        3
        + len(dias)
        + 3
    )

    ultima_columna = get_column_letter(
        total_columnas
    )


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


    # ==========================================================
    # DATOS
    # ==========================================================

    ws["A5"] = "CURSO:"
    ws["B5"] = curso

    ws["D5"] = "MES:"
    ws["E5"] = nombre_mes

    ws["G5"] = "AÑO:"
    ws["H5"] = anio


    ws["A5"].font = Font(bold=True)
    ws["D5"].font = Font(bold=True)
    ws["G5"].font = Font(bold=True)


    # ==========================================================
    # ENCABEZADOS TABLA
    # ==========================================================

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

        celda = ws.cell(
            row=fila_encabezado,
            column=columna
        )

        celda.value = (
            f"{dia['numero']}\n"
            f"{dia['dia_semana']}"
        )

        columna += 1


    ws.cell(
        row=fila_encabezado,
        column=columna,
        value="P"
    )

    ws.cell(
        row=fila_encabezado,
        column=columna + 1,
        value="A"
    )

    ws.cell(
        row=fila_encabezado,
        column=columna + 2,
        value="%"
    )


    # Estilo encabezados

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
            size=8
        )

        celda.fill = encabezado_fill

        celda.border = borde

        celda.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True
        )


    # ==========================================================
    # FILAS DE ALUMNOS
    # ==========================================================

    fila_excel = 8


    for numero, alumno in enumerate(
        alumnos,
        start=1
    ):

        presentes = 0

        ausentes = 0


        # Número

        ws.cell(
            row=fila_excel,
            column=1,
            value=numero
        )


        # Cédula

        ws.cell(
            row=fila_excel,
            column=2,
            value=alumno.cedula
        )


        # Alumno

        nombre_completo = (
            f"{alumno.apellidos}, "
            f"{alumno.nombres}"
        )

        ws.cell(
            row=fila_excel,
            column=3,
            value=nombre_completo
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


            # Fecha futura

            if fecha > hoy:

                celda.value = "-"

                celda.fill = pendiente_fill


            # Presente

            elif (
                asistencia
                and asistencia.hora_entrada
            ):

                celda.value = "P"

                celda.fill = presente_fill

                presentes += 1


            # Ausente

            else:

                celda.value = "A"

                celda.fill = ausente_fill

                ausentes += 1


            columna_dia += 1


        # ======================================================
        # TOTALES
        # ======================================================

        dias_computados = presentes + ausentes


        if dias_computados:

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
            column=columna_dia,
            value=presentes
        )

        ws.cell(
            row=fila_excel,
            column=columna_dia + 1,
            value=ausentes
        )

        ws.cell(
            row=fila_excel,
            column=columna_dia + 2,
            value=f"{porcentaje}%"
        )


        # ======================================================
        # ESTILO DE FILA
        # ======================================================

        for c in range(
            1,
            total_columnas + 1
        ):

            celda = ws.cell(
                row=fila_excel,
                column=c
            )

            celda.border = borde

            celda.font = Font(
                size=7
            )

            celda.alignment = Alignment(
                horizontal=(
                    "left"
                    if c == 3
                    else "center"
                ),
                vertical="center"
            )


        fila_excel += 1


    # ==========================================================
    # ANCHO DE COLUMNAS
    # ==========================================================

    ws.column_dimensions["A"].width = 4

    ws.column_dimensions["B"].width = 10

    ws.column_dimensions["C"].width = 32


    for columna_dia in range(
        4,
        4 + len(dias)
    ):

        letra = get_column_letter(
            columna_dia
        )

        ws.column_dimensions[
            letra
        ].width = 4


    for c in range(
        4 + len(dias),
        total_columnas + 1
    ):

        letra = get_column_letter(c)

        ws.column_dimensions[
            letra
        ].width = 6


    # ==========================================================
    # ALTURAS
    # ==========================================================

    ws.row_dimensions[1].height = 20
    ws.row_dimensions[2].height = 18
    ws.row_dimensions[3].height = 22
    ws.row_dimensions[7].height = 25


    # ==========================================================
    # CONGELAR ENCABEZADO
    # ==========================================================

    ws.freeze_panes = "D8"


    # ==========================================================
    # RESPUESTA HTTP
    # ==========================================================

    response = HttpResponse(
        content_type=(
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )

    nombre_archivo = (
        f"asistencia_"
        f"{curso.replace(' ', '_')}_"
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

    return HttpResponse(
        "La exportación Excel será adaptada "
        "al nuevo sistema de entrada y salida."
    )


# ============================================================
# EXPORTAR PDF
#
# Se deja temporalmente disponible para que Django
# encuentre la función. Luego adaptaremos el PDF definitivo.
# ============================================================

def exportar_reporte_mensual_pdf(request):

    return HttpResponse(
        "La exportación PDF será adaptada "
        "al nuevo sistema de entrada y salida."
    )