from django.db import models


# ============================================================
# ALUMNOS
# ============================================================

class Alumno(models.Model):

    TURNO_CHOICES = [
        ("MAÑANA", "Mañana"),
        ("TARDE", "Tarde"),
        ("NOCHE", "Noche"),
    ]

    cedula = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de cédula",
    )

    nombres = models.CharField(
        max_length=100,
        verbose_name="Nombres",
    )

    apellidos = models.CharField(
        max_length=100,
        verbose_name="Apellidos",
    )

    curso = models.CharField(
        max_length=50,
        verbose_name="Curso",
    )

    seccion = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Sección",
    )

    especialidad = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Especialidad",
    )

    turno = models.CharField(
        max_length=10,
        choices=TURNO_CHOICES,
        default="MAÑANA",
        verbose_name="Turno",
    )

    telefono = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Teléfono",
    )

    nombre_tutor = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Nombre del padre/madre o tutor",
    )

    correo_tutor = models.EmailField(
        blank=True,
        verbose_name="Correo del padre/madre o tutor",
    )

    enviar_reporte_mensual = models.BooleanField(
        default=True,
        verbose_name="Enviar informe mensual",
    )
    uid_rfid = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        verbose_name="UID RFID",
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Alumno activo",
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro",
    )

    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
        ordering = ["apellidos", "nombres"]

    @property
    def nombre(self):
        return f"{self.apellidos}, {self.nombres}"

    def __str__(self):
        return f"{self.apellidos}, {self.nombres} - {self.cedula}"


# ============================================================
# MATERIAS
# ============================================================

class Materia(models.Model):

    nombre = models.CharField(
        max_length=100,
        unique=True,
    )

    activo = models.BooleanField(
        default=True,
    )

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materias"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


# ============================================================
# HORARIOS
# ============================================================

class HorarioClase(models.Model):

    DIAS = [
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miércoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    anio_lectivo = models.PositiveIntegerField(
        default=2026,
        verbose_name="Año lectivo",
    )

    curso = models.CharField(
        max_length=50,
        default="1° BTI",
        verbose_name="Curso",
    )

    dia_semana = models.IntegerField(
        choices=DIAS,
        verbose_name="Día",
    )

    hora_inicio = models.TimeField(
        verbose_name="Hora de inicio",
    )

    hora_fin = models.TimeField(
        verbose_name="Hora de finalización",
    )

    materia = models.ForeignKey(
        Materia,
        on_delete=models.PROTECT,
        related_name="horarios",
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Horario activo",
    )

    class Meta:
        verbose_name = "Horario de clase"
        verbose_name_plural = "Horarios de clases"
        ordering = [
            "dia_semana",
            "hora_inicio",
        ]

    def __str__(self):

        return (
            f"{self.get_dia_semana_display()} | "
            f"{self.curso} | "
            f"{self.materia.nombre} | "
            f"{self.hora_inicio:%H:%M} - "
            f"{self.hora_fin:%H:%M}"
        )


# ============================================================
# CLASE MANUAL / EXTRAORDINARIA
# ============================================================

class ClaseActiva(models.Model):

    materia = models.ForeignKey(
        Materia,
        on_delete=models.PROTECT,
        related_name="clases_activas",
    )

    activa = models.BooleanField(
        default=True,
    )

    iniciada = models.DateTimeField(
        auto_now_add=True,
    )

    finalizada = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Clase manual"
        verbose_name_plural = "Clases manuales"
        ordering = ["-iniciada"]

    def __str__(self):

        estado = (
            "ACTIVA"
            if self.activa
            else "FINALIZADA"
        )

        return (
            f"{self.materia.nombre} - "
            f"{estado}"
        )


# ============================================================
# ASISTENCIA
# ============================================================

class Asistencia(models.Model):

    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.CASCADE,
        related_name="asistencias",
    )

    materia = models.ForeignKey(
        Materia,
        on_delete=models.PROTECT,
        related_name="asistencias",
        null=True,
        blank=True,
    )

    fecha = models.DateField()

    hora = models.TimeField()

    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        ordering = [
            "-fecha",
            "-hora",
        ]

    def __str__(self):

        materia = (
            self.materia.nombre
            if self.materia
            else "Sin materia"
        )

        return (
            f"{self.alumno} - "
            f"{materia} - "
            f"{self.fecha}"
        )
class ReporteMensualEnviado(models.Model):

    ESTADOS = [
        ("ENVIADO", "Enviado"),
        ("ERROR", "Error"),
    ]

    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.CASCADE,
        related_name="reportes_mensuales_enviados",
    )

    mes = models.PositiveSmallIntegerField()

    anio = models.PositiveIntegerField()

    correo = models.EmailField()

    fecha_envio = models.DateTimeField(
        auto_now_add=True
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="ENVIADO",
    )

    detalle = models.TextField(
        blank=True
    )

    class Meta:

        verbose_name = "Informe mensual enviado"
        verbose_name_plural = "Informes mensuales enviados"

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "alumno",
                    "mes",
                    "anio",
                ],
                name="reporte_mensual_unico",
            )

        ]

    def __str__(self):

        return (
            f"{self.alumno} - "
            f"{self.mes}/{self.anio} - "
            f"{self.estado}"
        )