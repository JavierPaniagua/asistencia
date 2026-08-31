from asistencia.models import Alumno


# ============================================================
# CURSO
# ============================================================
# Cambia solamente esta línea si corresponde a otro curso.

CURSO = "1° BTI"


# ============================================================
# ALUMNOS
# ============================================================

alumnos = [

    {
        "cedula": "6650076",
        "nombre": "ACOSTA ZARATE, ANDERSON ADALBERTO",
    },

    {
        "cedula": "6993657",
        "nombre": "AMARILLA ROJAS, FEDERICO DANIEL",
    },

    {
        "cedula": "7397848",
        "nombre": "AVILA TORRES, XIMENA LUJAN",
    },

    {
        "cedula": "7025514",
        "nombre": "AYALA GONZALEZ, EDGAR GIULIANO",
    },

    {
        "cedula": "7361384",
        "nombre": "BAEZ ROA, LUANA LIZARELLA",
    },

    {
        "cedula": "6644742",
        "nombre": "BENITEZ AYALA, REBECA BELEN",
    },

    {
        "cedula": "7489738",
        "nombre": "BENITEZ BENITEZ, YEMIMA ESTHER",
    },

    {
        "cedula": "7458871",
        "nombre": "CABRERA ALZERRECA, JORGE GABRIEL",
    },

    {
        "cedula": "7768149",
        "nombre": "CABRERA SANCHEZ, NELSON IVAN DEJESUS",
    },

    {
        "cedula": "7331356",
        "nombre": "CAÑETE NOGUERA, FRANCO GABRIEL",
    },

    {
        "cedula": "7320176",
        "nombre": "DOMINGUEZ FERREIRA, ESTEBAN DAVID JOSUE",
    },

    {
        "cedula": "7317344",
        "nombre": "GAVILAN RIQUELME, KENIA MARIA",
    },

    {
        "cedula": "7779217",
        "nombre": "GONZALEZ GIMENEZ, ULISES EMMANUEL",
    },

    {
        "cedula": "6863586",
        "nombre": "MALDONADO MEZA, CARLOS MARTIN",
    },

    {
        "cedula": "6873276",
        "nombre": "MANCUELLO BENITEZ, TOBIAS ALEXANDER",
    },

    {
        "cedula": "7089647",
        "nombre": "MARTINEZ GIMENEZ, CARLOS EMANUEL",
    },

    {
        "cedula": "7814469",
        "nombre": "NUÑEZ FLORES, MILAGROS ISABEL",
    },

    {
        "cedula": "6989374",
        "nombre": "NUÑEZ PEDROZO, JOSHUA BENJAMIN",
    },

    {
        "cedula": "7017143",
        "nombre": "OJEDA CANO, JOSIAS HANIEL",
    },

    {
        "cedula": "6786264",
        "nombre": "OLMEDO CARDOZO, ACSA PERLA NAYELI",
    },

    {
        "cedula": "6868419",
        "nombre": "RAMOS TORRES, FERNANDO JAVIER",
    },

    {
        "cedula": "6702622",
        "nombre": "RIQUELME CHAVEZ, RENE NICOLAS",
    },

    {
        "cedula": "7435765",
        "nombre": "ROJAS ALMADA, ALAN EZEQUIEL",
    },

    {
        "cedula": "6779978",
        "nombre": "SANDOVAL ESPINOLA, FLORENCIO RODRIGO",
    },

    {
        "cedula": "6881469",
        "nombre": "SANTANDER ORTEGA, JORGE MATHIAS",
    },

    {
        "cedula": "7045262",
        "nombre": "TORRES BARRIOS, MARIA BELEN",
    },

    {
        "cedula": "6765670",
        "nombre": "VEGA FLEYTAS, SANTINO DAVID SEBASTIAN",
    },

    {
        "cedula": "6923504",
        "nombre": "VIERA GAVILAN, LUZ MIGUELA",
    },

]


# ============================================================
# CARGAR EN LA BASE DE DATOS
# ============================================================

creados = 0
actualizados = 0


for datos in alumnos:

    alumno, creado = Alumno.objects.update_or_create(

        cedula=datos["cedula"],

        defaults={
            "nombre": datos["nombre"],
            "curso": CURSO,
            "activo": True,
        }

    )

    if creado:

        creados += 1

        print(
            f"CREADO: {alumno.cedula} - {alumno.nombre}"
        )

    else:

        actualizados += 1

        print(
            f"ACTUALIZADO: {alumno.cedula} - {alumno.nombre}"
        )


print()
print("==============================================")
print("CARGA FINALIZADA")
print("==============================================")
print(f"Curso: {CURSO}")
print(f"Alumnos procesados: {len(alumnos)}")
print(f"Nuevos: {creados}")
print(f"Actualizados: {actualizados}")
print("==============================================")