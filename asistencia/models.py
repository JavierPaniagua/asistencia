from django.db import models
from django.utils import timezone


# ============================================================
# ALUMNO
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
        verbose_name="Número de cédula"
    )

    nombres = models.CharField(
        max_length=100,
        verbose_name="Nombres"
    )

    apellidos = models.CharField(
        max_length=100,
        verbose_name="Apellidos"
    )

    curso = models.CharField(
        max_length=50,
        verbose_name="Curso"
    )

    seccion = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Sección"
    )

    especialidad = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Especialidad"
    )

    turno = models.CharField(
        max_length=10,
        choices=TURNO_CHOICES,
        default="MAÑANA",
        verbose_name="Turno"
    )

    telefono = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Teléfono"
    )

    uid_rfid = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        verbose_name="UID RFID"
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Alumno activo"
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro",
        null=True,
        blank=True
    )

    # ========================================================
    # DATOS DEL PADRE / MADRE / TUTOR
    # ========================================================

    nombre_tutor = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Nombre del padre/madre o tutor"
    )

    correo_tutor = models.EmailField(
        blank=True,
        verbose_name="Correo del padre/madre o tutor"
    )

    enviar_reporte_mensual = models.BooleanField(
        default=True,
        verbose_name="Enviar informe mensual"
    )

    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"

        ordering = [
            "apellidos",
            "nombres"
        ]

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"

    @property
    def nombre(self):
        return f"{self.apellidos}, {self.nombres}"


# ============================================================
# MATERIA
#
# SE CONSERVA POR AHORA.
# YA NO SE UTILIZARÁ PARA MARCAR ASISTENCIA.
# NO LA BORRAMOS PARA EVITAR PROBLEMAS CON MIGRACIONES.
# ============================================================

class Materia(models.Model):

    nombre = models.CharField(
        max_length=100,
        unique=True
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = [
            "nombre"
        ]

        verbose_name = "Materia"
        verbose_name_plural = "Materias"

    def __str__(self):
        return self.nombre


# ============================================================
# HORARIO DE CLASE
#
# TAMBIÉN SE CONSERVA.
# YA NO SERÁ NECESARIO PARA REGISTRAR LA ENTRADA/SALIDA.
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
        verbose_name="Año lectivo"
    )

    curso = models.CharField(
        max_length=50,
        default="1° BTI",
        verbose_name="Curso"
    )

    dia_semana = models.IntegerField(
        choices=DIAS,
        verbose_name="Día"
    )

    hora_inicio = models.TimeField(
        verbose_name="Hora de inicio"
    )

    hora_fin = models.TimeField(
        verbose_name="Hora de finalización"
    )

    materia = models.ForeignKey(
        Materia,
        on_delete=models.PROTECT,
        related_name="horarios"
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Horario activo"
    )

    class Meta:
        verbose_name = "Horario de clase"
        verbose_name_plural = "Horarios de clases"

        ordering = [
            "dia_semana",
            "hora_inicio"
        ]

    def __str__(self):

        return (
            f"{self.get_dia_semana_display()} - "
            f"{self.hora_inicio.strftime('%H:%M')} - "
            f"{self.hora_fin.strftime('%H:%M')} - "
            f"{self.materia.nombre}"
        )


# ============================================================
# CLASE ACTIVA
#
# SE CONSERVA POR COMPATIBILIDAD.
# NO SE UTILIZARÁ PARA MARCAR ENTRADA/SALIDA.
# ============================================================

class ClaseActiva(models.Model):

    materia = models.ForeignKey(
        Materia,
        on_delete=models.PROTECT,
        related_name="clases_activas"
    )

    activa = models.BooleanField(
        default=True
    )

    iniciada = models.DateTimeField(
        auto_now_add=True
    )

    finalizada = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Clase activa"
        verbose_name_plural = "Clases activas"

        ordering = [
            "-iniciada"
        ]

    def __str__(self):

        if self.activa:
            estado = "ACTIVA"
        else:
            estado = "FINALIZADA"

        return (
            f"{self.materia.nombre} - "
            f"{estado}"
        )


# ============================================================
# ASISTENCIA
#
# NUEVA LÓGICA:
#
# 1 alumno = 1 registro por día
#
# Primera marcación:
#     HORA DE ENTRADA
#
# Segunda marcación:
#     HORA DE SALIDA
#
# Tercera marcación:
#     NO CREA OTRO REGISTRO
# ============================================================

class Asistencia(models.Model):

    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.CASCADE,
        related_name="asistencias"
    )

    fecha = models.DateField(
        default=timezone.localdate,
        verbose_name="Fecha"
    )

    hora_entrada = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Hora de entrada"
    )

    hora_salida = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Hora de salida"
    )

    observacion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Observación"
    )

    class Meta:

        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"

        ordering = [
            "-fecha",
            "alumno__apellidos",
            "alumno__nombres"
        ]

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "alumno",
                    "fecha"
                ],
                name="asistencia_unica_alumno_fecha"
            )

        ]

    def __str__(self):

        return (
            f"{self.alumno} - "
            f"{self.fecha}"
        )

    # ========================================================
    # ESTADO DE LA JORNADA DEL ALUMNO
    # ========================================================

    @property
    def estado(self):

        if (
            self.hora_entrada
            and self.hora_salida
        ):
            return "JORNADA COMPLETA"

        if self.hora_entrada:
            return "EN EL COLEGIO"

        return "SIN REGISTRO"

    # ========================================================
    # TEXTO DE ENTRADA
    # ========================================================

    @property
    def entrada_texto(self):

        if self.hora_entrada:

            return self.hora_entrada.strftime(
                "%H:%M:%S"
            )

        return "--:--"

    # ========================================================
    # TEXTO DE SALIDA
    # ========================================================

    @property
    def salida_texto(self):

        if self.hora_salida:

            return self.hora_salida.strftime(
                "%H:%M:%S"
            )

        return "--:--"