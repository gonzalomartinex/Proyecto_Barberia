from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Crear superusuario automáticamente si no existe'

    def handle(self, *args, **options):
        # Obtener credenciales de variables de entorno
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@barberia.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123456')
        
        self.stdout.write(f"Intentando crear superusuario: {username} ({email})")
        
        # Verificar si ya existe un usuario con ese username
        if User.objects.filter(username=username).exists():
            existing_user = User.objects.get(username=username)
            if existing_user.is_superuser:
                self.stdout.write(
                    self.style.WARNING(f'El superusuario "{username}" ya existe.')
                )
            else:
                # Convertir usuario existente en superusuario
                existing_user.is_superuser = True
                existing_user.is_staff = True
                existing_user.set_password(password)
                existing_user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Usuario "{username}" convertido a superusuario.')
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
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superusuario "{username}" creado exitosamente.')
            )
            self.stdout.write(f'Email: {email}')
            self.stdout.write(f'Username: {username}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear superusuario: {e}')
            )
