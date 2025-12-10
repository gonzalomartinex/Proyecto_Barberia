from django.db import models

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
