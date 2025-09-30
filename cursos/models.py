from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Curso(models.Model):
    titulo = models.CharField(max_length=200)
    dia = models.DateField(help_text="Fecha específica del curso")  # Fecha específica
    hora = models.TimeField()  # Formato HH:MM
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='cursos/', blank=True, null=True)
    inscriptos = models.ManyToManyField(User, through='InscripcionCurso', related_name='cursos_inscripto')
    
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
    
    def total_inscriptos(self):
        """Retorna el número total de inscriptos"""
        return self.inscriptos.count()

class InscripcionCurso(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('usuario', 'curso')
        verbose_name = 'Inscripción a Curso'
        verbose_name_plural = 'Inscripciones a Cursos'
        
    def __str__(self):
        return f"{self.usuario.nombre} - {self.curso.titulo}"
