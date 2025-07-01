from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

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

class Usuario(AbstractBaseUser, PermissionsMixin):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    fecha_nacimiento = models.DateField()
    fecha_registro = models.DateTimeField(default=timezone.now)
    estado = models.BooleanField(default=True)  # Habilitado/deshabilitado
    contador_faltas = models.PositiveIntegerField(default=0)
    es_administrador = models.BooleanField(default=False)
    foto_perfil = models.ImageField(upload_to='usuarios/perfiles/', blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido', 'telefono', 'fecha_nacimiento']
    objects = UsuarioManager()
    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.email})"

    def deshabilitar_si_faltas(self):
        if self.contador_faltas >= 3:
            self.estado = False
            self.save()

    def habilitar(self):
        self.estado = True
        self.contador_faltas = 0
        self.save()

class Barbero(models.Model):
    nombre = models.CharField(max_length=100)
    foto = models.ImageField(upload_to='barberos/fotos/', blank=True, null=True)
    fecha_nacimiento = models.DateField()
    bio = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    dni = models.CharField(max_length=20, unique=True)
    def __str__(self):
        return self.nombre

class TrabajoBarbero(models.Model):
    barbero = models.ForeignKey(Barbero, on_delete=models.CASCADE, related_name='trabajos')
    imagen = models.ImageField(upload_to='barberos/trabajos/')
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
