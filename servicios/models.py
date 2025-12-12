from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from utils.cloudinary_cleanup import eliminar_imagen_cloudinary

# Campos temporales para deploy - reemplazar utils
class ServicioBinaryImageField(models.ImageField):
    pass

class BinaryImageMixin:
    pass

# Create your models here.
class Servicio(models.Model, BinaryImageMixin):
    nombre = models.CharField(max_length=100)
    imagen = ServicioBinaryImageField(blank=True, null=True)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    orden = models.PositiveIntegerField(default=0, help_text="Orden de aparición en la página (menor número = aparece primero)")
    
    class Meta:
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre

@receiver(pre_delete, sender=Servicio)
def delete_servicio_image_from_cloudinary(sender, instance, **kwargs):
    """Elimina la imagen del servicio de Cloudinary antes de eliminar el registro"""
    if instance.imagen:
        eliminar_imagen_cloudinary(instance.imagen)
