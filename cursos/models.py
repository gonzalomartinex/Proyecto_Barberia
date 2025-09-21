from django.db import models
from django.core.validators import RegexValidator

class Curso(models.Model):
    titulo = models.CharField(max_length=200)
    dia = models.CharField(max_length=20)  # Ej: "Lunes", "Martes", etc.
    hora = models.TimeField()  # Formato HH:MM
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='cursos/', blank=True, null=True)
    
    class Meta:
        ordering = ['dia', 'hora']
        
    def __str__(self):
        return f"{self.titulo} - {self.dia} {self.hora}"
