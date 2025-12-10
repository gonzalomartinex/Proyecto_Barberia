from django.db import models
from utils.binary_image_fields import ProductoBinaryImageField
from utils.binary_image_mixin import BinaryImageMixin

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
