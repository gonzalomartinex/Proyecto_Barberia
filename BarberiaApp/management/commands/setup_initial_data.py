from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Cargar datos iniciales y crear superusuario'

    def handle(self, *args, **options):
        # Crear superusuario si no existe
        if not User.objects.filter(is_superuser=True).exists():
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@barberia.com')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
            
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(f'Superusuario "{username}" creado')
        
        # Cargar fixtures si existen
        from django.core.management import call_command
        import os
        
        fixtures_dir = 'fixtures'
        if os.path.exists(fixtures_dir):
            for fixture in ['barberos_inicial.json', 'servicios_inicial.json', 'productos_inicial.json']:
                fixture_path = os.path.join(fixtures_dir, fixture)
                if os.path.exists(fixture_path):
                    try:
                        call_command('loaddata', fixture_path)
                        self.stdout.write(f'Fixture {fixture} cargada')
                    except Exception as e:
                        self.stdout.write(f'Error cargando {fixture}: {e}')
