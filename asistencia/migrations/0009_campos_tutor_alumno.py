from django.db import migrations


def agregar_campos_tutor(apps, schema_editor):
    connection = schema_editor.connection

    with connection.cursor() as cursor:

        cursor.execute("PRAGMA table_info(asistencia_alumno);")

        columnas = {
            fila[1]
            for fila in cursor.fetchall()
        }

        if "nombre_tutor" not in columnas:
            cursor.execute(
                """
                ALTER TABLE asistencia_alumno
                ADD COLUMN nombre_tutor varchar(150)
                NOT NULL DEFAULT ''
                """
            )

        if "correo_tutor" not in columnas:
            cursor.execute(
                """
                ALTER TABLE asistencia_alumno
                ADD COLUMN correo_tutor varchar(254)
                NOT NULL DEFAULT ''
                """
            )

        if "enviar_reporte_mensual" not in columnas:
            cursor.execute(
                """
                ALTER TABLE asistencia_alumno
                ADD COLUMN enviar_reporte_mensual bool
                NOT NULL DEFAULT 1
                """
            )


def reversa(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("asistencia", "0008_reparar_tabla_alumno"),
    ]

    operations = [
        migrations.RunPython(
            agregar_campos_tutor,
            reversa,
        ),
    ]