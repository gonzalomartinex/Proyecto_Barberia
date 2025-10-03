from django.core.management.base import BaseCommand
from django.conf import settings
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'Migra imágenes existentes de media local a Cloudinary'

    def handle(self, *args, **options):
        self.stdout.write("🔄 Iniciando migración de imágenes a Cloudinary...")
        
        # Verificar si Cloudinary está configurado
        if not hasattr(settings, 'CLOUDINARY_STORAGE'):
            self.stdout.write(
                self.style.ERROR("❌ Cloudinary no está configurado. Asegúrate de tener las variables de entorno.")
            )
            return
            
        try:
            import cloudinary
            import cloudinary.uploader
        except ImportError:
            self.stdout.write(
                self.style.ERROR("❌ Cloudinary no está instalado. Ejecuta: pip install cloudinary")
            )
            return
            
        # Buscar todas las imágenes en media
        media_path = Path(settings.MEDIA_ROOT)
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        
        total_images = 0
        migrated_images = 0
        
        self.stdout.write(f"📁 Buscando imágenes en: {media_path}")
        
        for root, dirs, files in os.walk(media_path):
            # Saltar carpetas que no queremos migrar
            if any(skip in root for skip in ['static', 'staticfiles', 'Default', 'logo', 'carousel']):
                continue
                
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    total_images += 1
                    file_path = Path(root) / file
                    
                    # Calcular la ruta relativa desde media
                    relative_path = file_path.relative_to(media_path)
                    public_id = str(relative_path).replace('\\', '/').rsplit('.', 1)[0]
                    
                    try:
                        self.stdout.write(f"⬆️  Subiendo: {relative_path}")
                        
                        # Subir a Cloudinary
                        result = cloudinary.uploader.upload(
                            str(file_path),
                            public_id=public_id,
                            upload_preset='django-media',
                            overwrite=True
                        )
                        
                        migrated_images += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ Migrado: {relative_path} -> {result['secure_url']}")
                        )
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"❌ Error migrando {relative_path}: {e}")
                        )
                        
        self.stdout.write("=" * 60)
        self.stdout.write(f"📊 Resumen de migración:")
        self.stdout.write(f"   Total de imágenes encontradas: {total_images}")
        self.stdout.write(f"   Imágenes migradas exitosamente: {migrated_images}")
        self.stdout.write(f"   Errores: {total_images - migrated_images}")
        
        if migrated_images > 0:
            self.stdout.write(
                self.style.SUCCESS(f"🎉 Migración completada! Ve a Cloudinary Media Library para ver las imágenes.")
            )
        else:
            self.stdout.write(
                self.style.WARNING("⚠️  No se migraron imágenes. Verifica la configuración de Cloudinary.")
            )
