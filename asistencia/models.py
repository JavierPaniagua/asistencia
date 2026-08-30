from django.db import models


# ============================================================
# MODELO ALUMNO
# ============================================================

class Alumno(models.Model):

    cedula = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Cédula"
    )

    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre y apellido"
    )

    curso = models.CharField(
        max_length=50,
        verbose_name="Curso"
    )

    uid_rfid = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        null=True,
        verbose_name="UID RFID"
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} - {self.curso}"


# ============================================================
# MODELO ASISTENCIA
# ============================================================

class Asistencia(models.Model):

    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.CASCADE,
        related_name="asistencias",
        verbose_name="Alumno"
    )

    fecha = models.DateField(
        verbose_name="Fecha"
    )

    hora = models.TimeField(
        verbose_name="Hora"
    )

    estado = models.CharField(
        max_length=20,
        default="presente",
        verbose_name="Estado"
    )

    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"

        ordering = [
            "-fecha",
            "-hora"
        ]

        # Evita registrar dos veces
        # al mismo alumno en el mismo día
        constraints = [
            models.UniqueConstraint(
                fields=["alumno", "fecha"],
                name="asistencia_unica_por_dia"
            )
        ]

    def __str__(self):
        return (
            f"{self.alumno.nombre} - "
            f"{self.fecha} - "
            f"{self.hora}"
        )