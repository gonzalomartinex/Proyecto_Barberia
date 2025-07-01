from rest_framework import serializers
from .models import Usuario

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nombre', 'apellido', 'email', 'telefono', 'fecha_nacimiento', 'fecha_registro', 'estado', 'contador_faltas', 'es_administrador', 'foto_perfil']
