from datetime import datetime, timedelta

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .models import Alumno, Asistencia


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

def reporte_mensual_curso(request):

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