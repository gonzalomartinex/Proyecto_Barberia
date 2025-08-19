from django.db import models

class CarouselImage(models.Model):
    imagen = models.ImageField(upload_to='carousel/')
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"{self.orden}: {self.imagen.name}"
