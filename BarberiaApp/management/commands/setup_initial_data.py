from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os
from datetime import date

User = get_user_model()

class Command(BaseCommand):
    help = 'Cargar datos iniciales y crear superusuario'

    def handle(self, *args, **options):
        # Crear superusuario si no existe
        if not User.objects.filter(is_superuser=True).exists():
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@barberia.com')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123456')
            nombre = os.environ.get('DJANGO_SUPERUSER_NOMBRE', 'Admin')
            apellido = os.environ.get('DJANGO_SUPERUSER_APELLIDO', 'Sistema')
            telefono = os.environ.get('DJANGO_SUPERUSER_TELEFONO', '1234567890')
            
            try:
                User.objects.create_superuser(
                    email=email,
                    nombre=nombre,
                    apellido=apellido,
                    telefono=telefono,
                    fecha_nacimiento=date(1990, 1, 1),
                    password=password
                )
                self.stdout.write(f'Superusuario "{email}" creado')
            except Exception as e:
                self.stdout.write(f'Error creando superusuario: {e}')
        
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
        
        # Configurar carousel con imágenes por defecto
        try:
            call_command('setup_carousel')
            self.stdout.write('Carousel configurado')
        except Exception as e:
            self.stdout.write(f'Error configurando carousel: {e}')
