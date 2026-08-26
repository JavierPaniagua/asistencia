from django.db import models


class Alumno(models.Model):
    cedula = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    curso = models.CharField(max_length=50)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"


class TarjetaRFID(models.Model):
    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.CASCADE,
        related_name="tarjetas"
    )
    uid = models.CharField(max_length=50, unique=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.uid} - {self.alumno}"


class Asistencia(models.Model):
    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.CASCADE,
        related_name="asistencias"
    )
    fecha = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.alumno} - {self.fecha} {self.hora}"