from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os
from datetime import date

User = get_user_model()

class Command(BaseCommand):
    help = 'Crear superusuario automáticamente si no existe'

    def handle(self, *args, **options):
        # Obtener credenciales de variables de entorno
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@barberia.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123456')
        nombre = os.environ.get('DJANGO_SUPERUSER_NOMBRE', 'Admin')
        apellido = os.environ.get('DJANGO_SUPERUSER_APELLIDO', 'Sistema')
        telefono = os.environ.get('DJANGO_SUPERUSER_TELEFONO', '1234567890')
        
        self.stdout.write(f"Intentando crear superusuario: {email}")
        
        # Verificar si ya existe un usuario con ese email
        if User.objects.filter(email=email).exists():
            existing_user = User.objects.get(email=email)
            if existing_user.is_superuser:
                self.stdout.write(
                    self.style.WARNING(f'El superusuario "{email}" ya existe.')
                )
            else:
                # Convertir usuario existente en superusuario
                existing_user.is_superuser = True
                existing_user.is_staff = True
                existing_user.es_administrador = True
                existing_user.set_password(password)
                existing_user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Usuario "{email}" convertido a superusuario.')
                )
            return
        
        # Verificar si ya existe otro superusuario
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING('Ya existe un superusuario en el sistema.')
            )
            return
        
        # Crear superusuario
        try:
            user = User.objects.create_superuser(
                email=email,
                nombre=nombre,
                apellido=apellido,
                telefono=telefono,
                fecha_nacimiento=date(1990, 1, 1),  # Fecha por defecto
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superusuario "{email}" creado exitosamente.')
            )
            self.stdout.write(f'Email: {email}')
            self.stdout.write(f'Nombre: {nombre} {apellido}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear superusuario: {e}')
            )
