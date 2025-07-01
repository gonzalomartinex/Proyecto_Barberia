from django.db import models
from usuarios.models import Usuario, Barbero
from servicios.models import Servicio

class Turno(models.Model):
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('ocupado', 'Ocupado'),
        ('cancelado', 'Cancelado'),
        ('completado', 'Completado'),
    ]
    cliente = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='turnos')
    barbero = models.ForeignKey(Barbero, on_delete=models.CASCADE, related_name='turnos')
    fecha_hora = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='disponible')
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='turnos')
    def __str__(self):
        return f"{self.fecha_hora} - {self.barbero} - {self.estado}"
