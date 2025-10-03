from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Verificar usuarios existentes y superusuarios'

    def handle(self, *args, **options):
        self.stdout.write("=== USUARIOS EN LA BASE DE DATOS ===")
        
        # Listar todos los usuarios
        users = User.objects.all()
        if users.exists():
            for user in users:
                status = "SUPERUSUARIO" if user.is_superuser else "Usuario normal"
                self.stdout.write(f"- {user.email} ({user.nombre} {user.apellido}) [{status}]")
        else:
            self.stdout.write("No hay usuarios en la base de datos")
        
        self.stdout.write(f"\nTotal usuarios: {users.count()}")
        self.stdout.write(f"Total superusuarios: {User.objects.filter(is_superuser=True).count()}")
        
        # Mostrar variables de entorno
        self.stdout.write("\n=== VARIABLES DE ENTORNO ===")
        self.stdout.write(f"EMAIL: {os.environ.get('DJANGO_SUPERUSER_EMAIL', 'NO DEFINIDA')}")
        self.stdout.write(f"NOMBRE: {os.environ.get('DJANGO_SUPERUSER_NOMBRE', 'NO DEFINIDA')}")
        self.stdout.write(f"APELLIDO: {os.environ.get('DJANGO_SUPERUSER_APELLIDO', 'NO DEFINIDA')}")
        self.stdout.write(f"PASSWORD: {'***DEFINIDA***' if os.environ.get('DJANGO_SUPERUSER_PASSWORD') else 'NO DEFINIDA'}")
