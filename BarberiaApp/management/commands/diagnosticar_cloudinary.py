from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Diagnosticar configuración de Cloudinary'

    def handle(self, *args, **options):
        self.stdout.write("🔍 DIAGNÓSTICO DE CLOUDINARY")
        self.stdout.write("-" * 50)
        
        # Variables de entorno
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
        api_key = os.environ.get('CLOUDINARY_API_KEY')
        api_secret = os.environ.get('CLOUDINARY_API_SECRET')
        
        self.stdout.write(f"CLOUDINARY_CLOUD_NAME: {cloud_name}")
        self.stdout.write(f"CLOUDINARY_API_KEY: {api_key}")
        self.stdout.write(f"CLOUDINARY_API_SECRET: {'***' + api_secret[-4:] if api_secret else 'None'}")
        
        # Configuración de Django
        self.stdout.write(f"DEBUG: {settings.DEBUG}")
        self.stdout.write(f"DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}")
        
        # Verificar si Cloudinary está disponible
        try:
            import cloudinary
            self.stdout.write("✅ Cloudinary importado correctamente")
            self.stdout.write(f"Cloudinary config: {cloudinary.config()}")
        except ImportError:
            self.stdout.write("❌ Error importando Cloudinary")
        
        # Verificar apps instaladas
        if 'cloudinary_storage' in settings.INSTALLED_APPS:
            self.stdout.write("✅ cloudinary_storage en INSTALLED_APPS")
        else:
            self.stdout.write("❌ cloudinary_storage NO en INSTALLED_APPS")
            
        if 'cloudinary' in settings.INSTALLED_APPS:
            self.stdout.write("✅ cloudinary en INSTALLED_APPS")
        else:
            self.stdout.write("❌ cloudinary NO en INSTALLED_APPS")
