from rest_framework import serializers
from .models import Producto

class ProductoSerializer(serializers.ModelSerializer):
    imagen_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Producto
        fields = '__all__'
        
    def get_imagen_url(self, obj):
        """
        Devuelve la URL de Cloudinary para la imagen
        """
        if obj.imagen and hasattr(obj.imagen, 'url'):
            # Para Cloudinary, la URL ya es completa y accesible directamente
            return obj.imagen.url
        return None
