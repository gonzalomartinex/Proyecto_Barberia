from django.db import models

# Create your models here.
class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='servicios/imagenes/', blank=True, null=True)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    def __str__(self):
        return self.nombre
