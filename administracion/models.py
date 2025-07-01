from django.db import models
from usuarios.models import Usuario, Barbero
from servicios.models import Servicio

class RegistroServicios(models.Model):
    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='registros_servicios')
    barbero = models.ForeignKey(Barbero, on_delete=models.CASCADE, related_name='registros_servicios')
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='registros_servicios')
    fecha = models.DateTimeField()
    notas = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.fecha} - {self.cliente} - {self.servicio}"
