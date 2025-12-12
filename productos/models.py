from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from utils.cloudinary_cleanup import eliminar_imagen_cloudinary
import logging

logger = logging.getLogger(__name__)

# Campos temporales para deploy - reemplazar utils
class ProductoBinaryImageField(models.ImageField):
    pass

class BinaryImageMixin:
    pass

# Create your models here.
class Producto(models.Model, BinaryImageMixin):
    nombre = models.CharField(max_length=100)
    imagen = ProductoBinaryImageField(blank=True, null=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    orden = models.PositiveIntegerField(default=0, help_text="Orden de aparición en la página (menor número = aparece primero)")
    
    class Meta:
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre

# Señal para eliminar imagen de Cloudinary antes de eliminar el producto
@receiver(pre_delete, sender=Producto)
def eliminar_imagen_producto_cloudinary(sender, instance, **kwargs):
    """
    Elimina automáticamente la imagen del producto de Cloudinary
    antes de que el producto sea eliminado de la base de datos.
    """
    if instance.imagen:
        try:
            resultado = eliminar_imagen_cloudinary(instance.imagen)
            if resultado:
                logger.info(f"Imagen del producto '{instance.nombre}' eliminada de Cloudinary: {instance.imagen.name}")
            else:
                logger.warning(f"No se pudo eliminar la imagen del producto '{instance.nombre}' de Cloudinary: {instance.imagen.name}")
        except Exception as e:
            logger.error(f"Error al eliminar imagen del producto '{instance.nombre}' de Cloudinary: {str(e)}")
