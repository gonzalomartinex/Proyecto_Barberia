import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Copia archivos media a staticfiles para que WhiteNoise los sirva'

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        static_root = settings.STATIC_ROOT
        
        if not os.path.exists(media_root):
            self.stdout.write(
                self.style.WARNING(f'El directorio media no existe: {media_root}')
            )
            return
            
        # Crear directorio media dentro de staticfiles
        static_media_dir = os.path.join(static_root, 'media')
        
        if os.path.exists(static_media_dir):
            shutil.rmtree(static_media_dir)
            
        shutil.copytree(media_root, static_media_dir)
        
        self.stdout.write(
            self.style.SUCCESS(f'Archivos media copiados a {static_media_dir}')
        )
