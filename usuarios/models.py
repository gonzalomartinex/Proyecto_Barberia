from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

# Campos temporales para deploy - reemplazar utils
class PerfilBinaryImageField(models.ImageField):
    pass

class BarberoBinaryImageField(models.ImageField):
    pass

class BinaryImageMixin:
    pass

class UsuarioManager(BaseUserManager):
    def create_user(self, email, nombre, apellido, telefono, fecha_nacimiento, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, apellido=apellido, telefono=telefono, fecha_nacimiento=fecha_nacimiento, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre, apellido, telefono, fecha_nacimiento, password=None, **extra_fields):
        extra_fields.setdefault('es_administrador', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, nombre, apellido, telefono, fecha_nacimiento, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin, BinaryImageMixin):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    fecha_nacimiento = models.DateField()
    fecha_registro = models.DateTimeField(default=timezone.now)
    estado = models.BooleanField(default=True)  # Habilitado/deshabilitado
    contador_faltas = models.PositiveIntegerField(default=0)
    es_administrador = models.BooleanField(default=False)
    foto_perfil = PerfilBinaryImageField(blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  # Necesario para Django auth
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido', 'telefono', 'fecha_nacimiento']
    objects = UsuarioManager()
    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.email})"

    def get_foto_perfil_url(self):
        """Retorna la URL de la foto de perfil o la imagen por defecto si no tiene"""
        if self.has_image('foto_perfil'):
            return self.get_image_data_url('foto_perfil')
        return '/static/Default/perfil_default.png'

    def deshabilitar_si_faltas(self):
        if self.contador_faltas >= 3:
            self.estado = False
            self.save()

    def habilitar(self):
        self.estado = True
        self.contador_faltas = 0
        self.save()

class Barbero(models.Model, BinaryImageMixin):
    nombre = models.CharField(max_length=100)
    foto = BarberoBinaryImageField(blank=True, null=True)
    fecha_nacimiento = models.DateField()
    bio = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    dni = models.CharField(max_length=20, unique=True)
    orden = models.PositiveIntegerField(default=0, help_text="Orden de aparición en la página (menor número = aparece primero)")
    
    class Meta:
        ordering = ['orden', 'nombre']
        
    def __str__(self):
        return self.nombre

class TrabajoBarbero(models.Model, BinaryImageMixin):
    barbero = models.ForeignKey(Barbero, on_delete=models.CASCADE, related_name='trabajos')
    imagen = BarberoBinaryImageField()
    fecha = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Trabajo de {self.barbero.nombre} - {self.fecha.strftime('%Y-%m-%d')}"

class RedSocial(models.Model):
    barbero = models.ForeignKey(Barbero, on_delete=models.CASCADE, related_name='redes_sociales')
    url = models.URLField(max_length=255)
    nombre = models.CharField(max_length=50, blank=True)
    orden = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.nombre or self.url
