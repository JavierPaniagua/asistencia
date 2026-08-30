from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from .models import Alumno, Asistencia


# ============================================================
# ESTADO ACTUAL DE LA PANTALLA
# ============================================================
# Para nuestro sistema local funciona perfectamente.
# Cada vez que se lee una tarjeta, aquí se guarda el resultado.

estado_actual = {
    "evento_id": 0,
    "estado": "esperando",
    "nombre": "",
    "curso": "",
    "cedula": "",
    "uid": "",
    "fecha": "",
    "hora": "",
    "mensaje": "Esperando identificación..."
}


def actualizar_pantalla(
    estado,
    mensaje,
    nombre="",
    curso="",
    cedula="",
    uid="",
    fecha="",
    hora=""
):
    global estado_actual

    estado_actual = {
        "evento_id": int(timezone.now().timestamp() * 1000),
        "estado": estado,
        "nombre": nombre,
        "curso": curso,
        "cedula": cedula,
        "uid": uid,
        "fecha": fecha,
        "hora": hora,
        "mensaje": mensaje
    }


# ============================================================
# PANTALLA PRINCIPAL
# ============================================================

def pantalla(request):
    return render(
        request,
        "asistencia/pantalla.html"
    )


# ============================================================
# API RFID
# ============================================================

def registrar_rfid(request):

    uid = request.GET.get("uid", "")
    uid = uid.replace(" ", "").upper().strip()

    # --------------------------------------------------------
    # UID VACÍO
    # --------------------------------------------------------

    if not uid:

        return JsonResponse({
            "estado": "error",
            "mensaje": "No se recibió UID"
        })


    # --------------------------------------------------------
    # BUSCAR ALUMNO
    # --------------------------------------------------------

    try:

        alumno = Alumno.objects.get(
            uid_rfid=uid,
            activo=True
        )

    except Alumno.DoesNotExist:

        actualizar_pantalla(
            estado="no_encontrado",
            mensaje="Tarjeta RFID no registrada",
            uid=uid
        )

        return JsonResponse({
            "estado": "no_encontrado",
            "uid": uid,
            "mensaje": "Tarjeta RFID no registrada"
        })


    # --------------------------------------------------------
    # FECHA Y HORA
    # --------------------------------------------------------

    ahora = timezone.localtime()
    hoy = ahora.date()


    # --------------------------------------------------------
    # VERIFICAR ASISTENCIA DEL DÍA
    # --------------------------------------------------------

    asistencia_existente = Asistencia.objects.filter(
        alumno=alumno,
        fecha=hoy
    ).first()


    # --------------------------------------------------------
    # YA ESTABA REGISTRADO
    # --------------------------------------------------------

    if asistencia_existente:

        fecha = asistencia_existente.fecha.strftime(
            "%d/%m/%Y"
        )

        hora = asistencia_existente.hora.strftime(
            "%H:%M:%S"
        )

        actualizar_pantalla(
            estado="ya_registrado",
            nombre=alumno.nombre,
            curso=alumno.curso,
            cedula=alumno.cedula,
            uid=uid,
            fecha=fecha,
            hora=hora,
            mensaje="Su asistencia ya fue registrada hoy"
        )

        return JsonResponse({
            "estado": "ya_registrado",
            "nombre": alumno.nombre,
            "curso": alumno.curso,
            "cedula": alumno.cedula,
            "uid": uid,
            "fecha": fecha,
            "hora": hora,
            "mensaje": "La asistencia ya fue registrada hoy"
        })


    # --------------------------------------------------------
    # NUEVA ASISTENCIA
    # --------------------------------------------------------

    asistencia = Asistencia.objects.create(
        alumno=alumno,
        fecha=hoy,
        hora=ahora.time(),
        estado="presente"
    )

    fecha = asistencia.fecha.strftime(
        "%d/%m/%Y"
    )

    hora = asistencia.hora.strftime(
        "%H:%M:%S"
    )


    # --------------------------------------------------------
    # ACTUALIZAR PANTALLA
    # --------------------------------------------------------

    actualizar_pantalla(
        estado="registrado",
        nombre=alumno.nombre,
        curso=alumno.curso,
        cedula=alumno.cedula,
        uid=uid,
        fecha=fecha,
        hora=hora,
        mensaje="Asistencia registrada correctamente"
    )


    # --------------------------------------------------------
    # RESPUESTA AL ESP32
    # --------------------------------------------------------

    return JsonResponse({
        "estado": "registrado",
        "nombre": alumno.nombre,
        "curso": alumno.curso,
        "cedula": alumno.cedula,
        "uid": uid,
        "fecha": fecha,
        "hora": hora,
        "mensaje": "Asistencia registrada correctamente"
    })


# ============================================================
# API ESTADO DE PANTALLA
# ============================================================

def estado_pantalla(request):

    return JsonResponse(
        estado_actual
    )


# ============================================================
# PRUEBA MANUAL POR CÉDULA
# ============================================================

def probar_asistencia(request, cedula):

    try:

        alumno = Alumno.objects.get(
            cedula=cedula,
            activo=True
        )

    except Alumno.DoesNotExist:

        actualizar_pantalla(
            estado="no_encontrado",
            mensaje="Alumno no encontrado"
        )

        return JsonResponse({
            "estado": "no_encontrado",
            "cedula": cedula,
            "mensaje": "Alumno no encontrado"
        })


    ahora = timezone.localtime()
    hoy = ahora.date()

    asistencia_existente = Asistencia.objects.filter(
        alumno=alumno,
        fecha=hoy
    ).first()


    # --------------------------------------------------------
    # YA REGISTRADO
    # --------------------------------------------------------

    if asistencia_existente:

        fecha = asistencia_existente.fecha.strftime(
            "%d/%m/%Y"
        )

        hora = asistencia_existente.hora.strftime(
            "%H:%M:%S"
        )

        actualizar_pantalla(
            estado="ya_registrado",
            nombre=alumno.nombre,
            curso=alumno.curso,
            cedula=alumno.cedula,
            uid=alumno.uid_rfid or "",
            fecha=fecha,
            hora=hora,
            mensaje="Su asistencia ya fue registrada hoy"
        )

        return JsonResponse({
            "estado": "ya_registrado",
            "nombre": alumno.nombre,
            "curso": alumno.curso,
            "cedula": alumno.cedula,
            "fecha": fecha,
            "hora": hora,
            "mensaje": "La asistencia ya fue registrada hoy"
        })


    # --------------------------------------------------------
    # REGISTRAR
    # --------------------------------------------------------

    asistencia = Asistencia.objects.create(
        alumno=alumno,
        fecha=hoy,
        hora=ahora.time(),
        estado="presente"
    )

    fecha = asistencia.fecha.strftime(
        "%d/%m/%Y"
    )

    hora = asistencia.hora.strftime(
        "%H:%M:%S"
    )

    actualizar_pantalla(
        estado="registrado",
        nombre=alumno.nombre,
        curso=alumno.curso,
        cedula=alumno.cedula,
        uid=alumno.uid_rfid or "",
        fecha=fecha,
        hora=hora,
        mensaje="Asistencia registrada correctamente"
    )

    return JsonResponse({
        "estado": "registrado",
        "nombre": alumno.nombre,
        "curso": alumno.curso,
        "cedula": alumno.cedula,
        "fecha": fecha,
        "hora": hora,
        "mensaje": "Asistencia registrada correctamente"
    })