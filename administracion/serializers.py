from rest_framework import serializers
from .models import RegistroServicios

class RegistroServiciosSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroServicios
        fields = '__all__'
