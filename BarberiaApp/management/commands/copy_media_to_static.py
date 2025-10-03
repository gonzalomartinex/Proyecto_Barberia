import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from BarberiaApp.media_config import DEFAULT_IMAGE_DIRS

class Command(BaseCommand):
    help = 'Copia solo las imágenes por defecto a staticfiles para que WhiteNoise las sirva'

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
        
        os.makedirs(static_media_dir, exist_ok=True)
        
        # Copiar solo los directorios de imágenes por defecto
        for dir_name in DEFAULT_IMAGE_DIRS:
            source_dir = os.path.join(media_root, dir_name)
            dest_dir = os.path.join(static_media_dir, dir_name)
            
            if os.path.exists(source_dir):
                shutil.copytree(source_dir, dest_dir)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Copiado: {dir_name}/ → static/media/{dir_name}/')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ No encontrado: {source_dir}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'🎉 Imágenes por defecto copiadas a {static_media_dir}')
        )
        
        self.stdout.write(
            self.style.INFO('📝 Las imágenes de usuarios se manejarán con Cloudinary')
        )
