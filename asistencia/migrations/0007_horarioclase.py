from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("asistencia", "0006_add_finalizada_claseactiva"),
    ]

    operations = [

        migrations.CreateModel(

            name="HorarioClase",

            fields=[

                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),

                (
                    "anio_lectivo",
                    models.PositiveIntegerField(
                        default=2026,
                        verbose_name="Año lectivo",
                    ),
                ),

                (
                    "curso",
                    models.CharField(
                        default="1° BTI",
                        max_length=50,
                        verbose_name="Curso",
                    ),
                ),

                (
                    "dia_semana",
                    models.IntegerField(
                        choices=[
                            (0, "Lunes"),
                            (1, "Martes"),
                            (2, "Miércoles"),
                            (3, "Jueves"),
                            (4, "Viernes"),
                            (5, "Sábado"),
                            (6, "Domingo"),
                        ],
                        verbose_name="Día",
                    ),
                ),

                (
                    "hora_inicio",
                    models.TimeField(
                        verbose_name="Hora de inicio",
                    ),
                ),

                (
                    "hora_fin",
                    models.TimeField(
                        verbose_name="Hora de finalización",
                    ),
                ),

                (
                    "activo",
                    models.BooleanField(
                        default=True,
                        verbose_name="Horario activo",
                    ),
                ),

                (
                    "materia",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="horarios",
                        to="asistencia.materia",
                    ),
                ),

            ],

            options={
                "verbose_name": "Horario de clase",
                "verbose_name_plural": "Horarios de clases",
                "ordering": [
                    "dia_semana",
                    "hora_inicio",
                ],
            },

        ),

    ]