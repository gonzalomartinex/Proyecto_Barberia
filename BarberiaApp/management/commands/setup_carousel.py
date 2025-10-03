#!/usr/bin/env python
"""
Management command para crear imágenes iniciales del carousel usando las imágenes por defecto
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import os

class Command(BaseCommand):
    help = 'Crea imágenes iniciales del carousel usando las imágenes por defecto'

    def handle(self, *args, **options):
        from BarberiaApp.models import CarouselImage
        
        self.stdout.write("🖼️  Configurando carousel con imágenes por defecto...")
        
        # Si ya hay imágenes en el carousel, no hacer nada
        if CarouselImage.objects.exists():
            self.stdout.write("✅ Ya existen imágenes en el carousel.")
            return
        
        # Directorio de imágenes por defecto del carousel
        carousel_dir = Path(settings.MEDIA_ROOT) / 'carousel'
        
        if not carousel_dir.exists():
            self.stdout.write("❌ No existe el directorio de carousel")
            return
        
        # Buscar imágenes en el directorio carousel
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
        carousel_images = []
        
        for filename in os.listdir(carousel_dir):
            if filename.lower().endswith(image_extensions):
                carousel_images.append(filename)
        
        # Crear entradas en la base de datos para cada imagen
        orden = 1
        created_count = 0
        
        for image_filename in sorted(carousel_images)[:6]:  # Máximo 6 imágenes
            try:
                # La ruta relativa desde MEDIA_ROOT
                image_path = f'carousel/{image_filename}'
                
                carousel_obj = CarouselImage.objects.create(
                    imagen=image_path,
                    orden=orden
                )
                
                self.stdout.write(f"✅ Creada imagen del carousel: {image_filename} (orden: {orden})")
                created_count += 1
                orden += 1
                
            except Exception as e:
                self.stdout.write(f"❌ Error al crear imagen {image_filename}: {str(e)}")
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n🎉 ¡Carousel configurado! Se crearon {created_count} imágenes.")
            )
        else:
            self.stdout.write(
                self.style.WARNING("⚠️  No se pudieron crear imágenes para el carousel.")
            )
