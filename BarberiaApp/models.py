from django.db import models
from utils.image_fields import OptimizedImageField

class CarouselImage(models.Model):
    imagen = OptimizedImageField(image_type='curso', upload_to='carousel/')
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"{self.orden}: {self.imagen.name}"
