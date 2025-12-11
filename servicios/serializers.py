from rest_framework import serializers
from .models import Servicio

class ServicioSerializer(serializers.ModelSerializer):
    imagen_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Servicio
        fields = '__all__'
        
    def get_imagen_url(self, obj):
        """
        Devuelve la URL completa de la imagen, manejando tanto URLs de Cloudinary como locales
        """
        if obj.imagen and hasattr(obj.imagen, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            else:
                return obj.imagen.url
        return None
