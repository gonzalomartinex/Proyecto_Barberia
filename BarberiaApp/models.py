from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from utils.cloudinary_cleanup import eliminar_imagen_cloudinary
import logging

logger = logging.getLogger(__name__)

# Campo temporal para deploy - reemplazar utils
class OptimizedImageField(models.ImageField):
    def __init__(self, *args, **kwargs):
        kwargs.pop('image_type', None)  # Remover parámetros personalizados
        super().__init__(*args, **kwargs)

class CarouselImage(models.Model):
    imagen = OptimizedImageField(image_type='curso', upload_to='carousel/')
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"{self.orden}: {self.imagen.name}"

@receiver(pre_delete, sender=CarouselImage)
def delete_carousel_image_from_cloudinary(sender, instance, **kwargs):
    """
    Elimina la imagen del carrusel de Cloudinary antes de eliminar el registro
    """
    if instance.imagen:
        try:
            success = eliminar_imagen_cloudinary(instance.imagen)
            if success:
                logger.info(f"🎠 Imagen de carrusel eliminada de Cloudinary: {instance.imagen.name}")
            else:
                logger.warning(f"⚠️ No se pudo eliminar imagen de carrusel de Cloudinary: {instance.imagen.name}")
        except Exception as e:
            logger.error(f"❌ Error eliminando imagen de carrusel de Cloudinary: {e}")
