from django.db import migrations


def reparar_tabla_alumno(apps, schema_editor):

    connection = schema_editor.connection

    with connection.cursor() as cursor:

        # ====================================================
        # OBTENER COLUMNAS EXISTENTES
        # ====================================================

        cursor.execute(
            "PRAGMA table_info(asistencia_alumno);"
        )

        columnas = {
            fila[1]
            for fila in cursor.fetchall()
        }


        # ====================================================
        # AGREGAR COLUMNAS QUE FALTAN
        # ====================================================

        if "cedula" not in columnas:
            cursor.execute(
                """
                ALTER TABLE asistencia_alumno
                ADD COLUMN cedula varchar(20)
                """
            )

        if "nombres" not in columnas:
            cursor.execute(
                """
                ALTER TABLE asistencia_alumno
                ADD COLUMN nombres varchar(100)
                NOT NULL DEFAULT ''
                """
            )

        if "apellidos" not in columnas:
            cursor.execute(
                """
                ALTER TABLE asistencia_alumno
                ADD COLUMN apellidos varchar(100)
                NOT NULL DEFAULT ''
                """
            )

        if "curso" not in columnas:
            cursor.execute(
                """
                ALTER TABLE asistencia_alumno
                ADD COLUMN curso varchar(50)
                NOT NULL DEFAULT '1° BTI'
                """
            )

        if "seccion" not in columnas:
            cursor.execute(
                """
                ALTER TABLE asistencia_alumno
                ADD COLUMN seccion varchar(20)
                NOT NULL DEFAULT ''
                """
            )

        if "especialidad" not in columnas:
            cursor.execute(
                """
                ALTER TABLE asistencia_alumno
                ADD COLUMN especialidad varchar(100)
                NOT NULL DEFAULT ''
                """
            )

        if "turno" not in columnas:
            cursor.execute(
                """
                ALTER TABLE asistencia_alumno
                ADD COLUMN turno varchar(10)
                NOT NULL DEFAULT 'TARDE'
                """
            )

        if "telefono" not in columnas:
            cursor.execute(
                """
                ALTER TABLE asistencia_alumno
                ADD COLUMN telefono varchar(30)
                NOT NULL DEFAULT ''
                """
            )

        if "uid_rfid" not in columnas:
            cursor.execute(
                """
                ALTER TABLE asistencia_alumno
                ADD COLUMN uid_rfid varchar(50)
                """
            )

        if "activo" not in columnas:
            cursor.execute(
                """
                ALTER TABLE asistencia_alumno
                ADD COLUMN activo bool
                NOT NULL DEFAULT 1
                """
            )

        if "fecha_registro" not in columnas:
            cursor.execute(
                """
                ALTER TABLE asistencia_alumno
                ADD COLUMN fecha_registro datetime
                """
            )


        # ====================================================
        # ÍNDICES ÚNICOS
        # ====================================================

        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            asistencia_alumno_cedula_unica
            ON asistencia_alumno(cedula)
            """
        )

        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            asistencia_alumno_uid_rfid_unico
            ON asistencia_alumno(uid_rfid)
            WHERE uid_rfid IS NOT NULL
            """
        )


def reversa(apps, schema_editor):
    # No eliminamos columnas para evitar pérdida de datos.
    pass


class Migration(migrations.Migration):

    dependencies = [
        (
            "asistencia",
            "0007_horarioclase",
        ),
    ]

    operations = [

        migrations.RunPython(
            reparar_tabla_alumno,
            reversa,
        ),

    ]