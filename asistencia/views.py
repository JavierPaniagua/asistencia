from datetime import timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from .models import Alumno, TarjetaRFID, Asistencia


# =========================================================
# ESTADO TEMPORAL DE LA PANTALLA
# =========================================================

ultimo_evento = {
    "estado": "espera",
    "nombre": "",
    "curso": "",
    "hora": "",
    "mensaje": "Esperando identificación...",
}

ultimo_evento_fecha = None


# =========================================================
# PANTALLA PRINCIPAL
# =========================================================

def pantalla_asistencia(request):
    return render(
        request,
        "asistencia/pantalla.html"
    )


# =========================================================
# ESTADO DE LA PANTALLA
# =========================================================

def estado_pantalla(request):

    global ultimo_evento
    global ultimo_evento_fecha

    # Si hubo un registro anterior
    if ultimo_evento_fecha is not None:

        tiempo_transcurrido = (
            timezone.now() - ultimo_evento_fecha
        )

        # Después de 5 segundos volver a espera
        if tiempo_transcurrido >= timedelta(seconds=5):

            ultimo_evento = {
                "estado": "espera",
                "nombre": "",
                "curso": "",
                "hora": "",
                "mensaje": "Esperando identificación...",
            }

            ultimo_evento_fecha = None

    return JsonResponse(ultimo_evento)


# =========================================================
# PRUEBA MANUAL POR CÉDULA
# =========================================================

def probar_asistencia(request, cedula):

    global ultimo_evento
    global ultimo_evento_fecha

    hora_actual = timezone.localtime()

    try:

        alumno = Alumno.objects.get(
            cedula=cedula,
            activo=True
        )

    except Alumno.DoesNotExist:

        ultimo_evento = {
            "estado": "error",
            "nombre": "",
            "curso": "",
            "hora": hora_actual.strftime("%H:%M:%S"),
            "mensaje": "Alumno no encontrado",
        }

        ultimo_evento_fecha = timezone.now()

        return JsonResponse(ultimo_evento)


    # =====================================================
    # FECHA ACTUAL
    # =====================================================

    hoy = timezone.localdate()


    # =====================================================
    # REGISTRAR ASISTENCIA
    # =====================================================

    asistencia, creada = Asistencia.objects.get_or_create(
        alumno=alumno,
        fecha=hoy
    )


    # =====================================================
    # ASISTENCIA NUEVA
    # =====================================================

    if creada:

        ultimo_evento = {
            "estado": "registrado",

            "nombre":
                f"{alumno.nombre} {alumno.apellido}",

            "curso":
                alumno.curso,

            "hora":
                hora_actual.strftime("%H:%M:%S"),

            "mensaje":
                "Asistencia registrada correctamente",
        }


    # =====================================================
    # ASISTENCIA DUPLICADA
    # =====================================================

    else:

        ultimo_evento = {
            "estado": "duplicado",

            "nombre":
                f"{alumno.nombre} {alumno.apellido}",

            "curso":
                alumno.curso,

            "hora":
                hora_actual.strftime("%H:%M:%S"),

            "mensaje":
                "La asistencia ya fue registrada hoy",
        }


    ultimo_evento_fecha = timezone.now()

    return JsonResponse(ultimo_evento)