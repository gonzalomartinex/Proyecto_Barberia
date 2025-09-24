from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone

class Curso(models.Model):
    titulo = models.CharField(max_length=200)
    dia = models.DateField(help_text="Fecha específica del curso")  # Fecha específica
    hora = models.TimeField()  # Formato HH:MM
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='cursos/', blank=True, null=True)
    
    class Meta:
        ordering = ['dia', 'hora']
        
    def __str__(self):
        return f"{self.titulo} - {self.dia.strftime('%d/%m/%Y')} {self.hora}"
    
    @property
    def dia_formateado(self):
        """Retorna el día en formato: 'Miércoles 17/10/2024'"""
        dias_semana = {
            0: 'Lunes',
            1: 'Martes', 
            2: 'Miércoles',
            3: 'Jueves',
            4: 'Viernes',
            5: 'Sábado',
            6: 'Domingo'
        }
        nombre_dia = dias_semana[self.dia.weekday()]
        fecha_formateada = self.dia.strftime('%d/%m/%Y')
        return f"{nombre_dia} {fecha_formateada}"
