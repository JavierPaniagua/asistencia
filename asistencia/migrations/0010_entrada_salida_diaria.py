from django.db import migrations, models
import django.utils.timezone


def preparar_asistencias(apps, schema_editor):
    """
    Antes de imponer una sola asistencia por alumno y fecha,
    consolidamos posibles registros repetidos del sistema anterior.

    Conservamos el primer registro del alumno en cada fecha.
    """

    Asistencia = apps.get_model("asistencia", "Asistencia")

    registros = (
        Asistencia.objects
        .all()
        .order_by(
            "alumno_id",
            "fecha",
            "hora",
            "id"
        )
    )

    vistos = set()

    for registro in registros:

        clave = (
            registro.alumno_id,
            registro.fecha
        )

        if clave in vistos:
            registro.delete()
        else:
            vistos.add(clave)


class Migration(migrations.Migration):

    dependencies = [
        (
            "asistencia",
            "0009_campos_tutor_alumno"
        ),
    ]

    operations = [

        # ====================================================
        # 1. CONSOLIDAR REGISTROS ANTIGUOS
        # ====================================================

        migrations.RunPython(
            preparar_asistencias,
            migrations.RunPython.noop
        ),

        # ====================================================
        # 2. RENOMBRAR HORA -> HORA_ENTRADA
        #
        # De esta manera NO perdemos la antigua hora.
        # ====================================================

        migrations.RenameField(
            model_name="asistencia",
            old_name="hora",
            new_name="hora_entrada",
        ),

        # ====================================================
        # 3. MODIFICAR HORA_ENTRADA
        # ====================================================

        migrations.AlterField(
            model_name="asistencia",
            name="hora_entrada",
            field=models.TimeField(
                blank=True,
                null=True,
                verbose_name="Hora de entrada"
            ),
        ),

        # ====================================================
        # 4. AGREGAR HORA DE SALIDA
        # ====================================================

        migrations.AddField(
            model_name="asistencia",
            name="hora_salida",
            field=models.TimeField(
                blank=True,
                null=True,
                verbose_name="Hora de salida"
            ),
        ),

        # ====================================================
        # 5. AGREGAR OBSERVACIÓN
        # ====================================================

        migrations.AddField(
            model_name="asistencia",
            name="observacion",
            field=models.CharField(
                blank=True,
                max_length=200,
                verbose_name="Observación"
            ),
        ),

        # ====================================================
        # 6. ELIMINAR MATERIA DE LA ASISTENCIA
        # ====================================================

        migrations.RemoveField(
            model_name="asistencia",
            name="materia",
        ),

        # ====================================================
        # 7. FECHA
        # ====================================================

        migrations.AlterField(
            model_name="asistencia",
            name="fecha",
            field=models.DateField(
                default=django.utils.timezone.localdate,
                verbose_name="Fecha"
            ),
        ),

        # ====================================================
        # 8. UNA SOLA ASISTENCIA POR ALUMNO Y DÍA
        # ====================================================

        migrations.AddConstraint(
            model_name="asistencia",
            constraint=models.UniqueConstraint(
                fields=(
                    "alumno",
                    "fecha"
                ),
                name="asistencia_unica_alumno_fecha"
            ),
        ),

        # ====================================================
        # 9. OPCIONES
        # ====================================================

        migrations.AlterModelOptions(
            name="asistencia",
            options={
                "ordering": [
                    "-fecha",
                    "alumno__apellidos",
                    "alumno__nombres"
                ],
                "verbose_name": "Asistencia",
                "verbose_name_plural": "Asistencias",
            },
        ),
    ]