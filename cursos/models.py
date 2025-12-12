from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from utils.cloudinary_cleanup import eliminar_imagen_cloudinary

# Campos temporales para deploy - reemplazar utils
class CursoBinaryImageField(models.ImageField):
    pass

class BinaryImageMixin:
    pass

User = get_user_model()

class Curso(models.Model, BinaryImageMixin):
    titulo = models.CharField(max_length=200)
    dia = models.DateField(help_text="Fecha específica del curso")  # Fecha específica
    hora = models.TimeField()  # Formato HH:MM
    descripcion = models.TextField()
    imagen = CursoBinaryImageField(blank=True, null=True)
    inscriptos = models.ManyToManyField(User, through='InscripcionCurso', related_name='cursos_inscripto')
    
    class Meta:
        ordering = ['-dia', '-hora']
        
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
    
    def curso_pasado(self):
        """Verifica si el curso ya pasó (fecha y hora)"""
        from datetime import datetime, time
        from django.utils import timezone
        
        # Verificar que tengamos fecha y hora válidas
        if not self.dia or not self.hora:
            return False  # Si no tiene fecha/hora, consideramos que no ha pasado
        
        try:
            # Combinar fecha y hora del curso
            curso_datetime = timezone.make_aware(
                datetime.combine(self.dia, self.hora),
                timezone.get_current_timezone()
            )
            
            # Comparar con la fecha y hora actual
            return timezone.now() > curso_datetime
        except (ValueError, TypeError):
            # En caso de cualquier error, consideramos que no ha pasado
            return False

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

@receiver(pre_delete, sender=Curso)
def delete_curso_image_from_cloudinary(sender, instance, **kwargs):
    """Elimina la imagen del curso de Cloudinary antes de eliminar el registro"""
    if instance.imagen:
        eliminar_imagen_cloudinary(instance.imagen)

@receiver(pre_save, sender=Curso)
def delete_old_curso_image_on_change(sender, instance, **kwargs):
    """Elimina la imagen anterior del curso de Cloudinary cuando se cambia o se elimina"""
    if instance.pk:  # Solo para actualizaciones, no para creaciones nuevas
        try:
            old_curso = Curso.objects.get(pk=instance.pk)
            # Si había imagen anterior y ahora es diferente o está vacía
            if old_curso.imagen and (not instance.imagen or old_curso.imagen != instance.imagen):
                eliminar_imagen_cloudinary(old_curso.imagen)
        except Curso.DoesNotExist:
            pass
