import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Copia solo las imágenes por defecto a staticfiles para que WhiteNoise las sirva'

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        static_root = settings.STATIC_ROOT
        
        # Directorios de imágenes por defecto
        default_dirs = ['Default', 'logo', 'carousel']
        
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
        for dir_name in default_dirs:
            source_dir = os.path.join(media_root, dir_name)
            dest_dir = os.path.join(static_media_dir, dir_name)
            
            if os.path.exists(source_dir):
                try:
                    shutil.copytree(source_dir, dest_dir)
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Copiado: {dir_name}/')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error copiando {dir_name}: {e}')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ No encontrado: {dir_name}/')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'🎉 Proceso completado')
        )
