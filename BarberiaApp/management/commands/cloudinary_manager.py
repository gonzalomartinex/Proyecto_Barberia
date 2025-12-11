from django.core.management.base import BaseCommand
from utils.cloudinary_cleanup import cleanup_orphaned_cloudinary_images, extract_public_id_from_url, delete_from_cloudinary
from BarberiaApp.models import CarouselImage
from servicios.models import Servicio
from usuarios.models import Barbero
from cursos.models import Curso
import cloudinary.api
import logging

class Command(BaseCommand):
    help = 'Gestiona la limpieza de imágenes en Cloudinary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Eliminar imágenes huérfanas de Cloudinary',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Listar todas las imágenes en Cloudinary y su estado',
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Probar la funcionalidad sin hacer cambios reales',
        )
        parser.add_argument(
            '--delete-public-id',
            type=str,
            help='Eliminar una imagen específica por su public_id',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== GESTIÓN DE IMÁGENES CLOUDINARY ==="))
        
        if options['delete_public_id']:
            # Eliminar imagen específica
            public_id = options['delete_public_id']
            self.stdout.write(f"Eliminando imagen: {public_id}")
            success = delete_from_cloudinary(public_id)
            if success:
                self.stdout.write(self.style.SUCCESS(f"✅ Imagen eliminada: {public_id}"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ No se pudo eliminar: {public_id}"))
            return

        if options['list']:
            # Listar todas las imágenes
            self._list_images()

        if options['cleanup']:
            # Limpiar imágenes huérfanas
            if options['test']:
                self.stdout.write(self.style.WARNING("MODO TEST - No se eliminarán imágenes"))
                self._test_cleanup()
            else:
                self.stdout.write("Iniciando limpieza de imágenes huérfanas...")
                deleted_count = cleanup_orphaned_cloudinary_images()
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Limpieza completada. {deleted_count} imágenes eliminadas.")
                )
        
        if not any(options.values()):
            self.stdout.write("💡 Opciones disponibles:")
            self.stdout.write("   --list: Listar todas las imágenes")
            self.stdout.write("   --cleanup: Limpiar imágenes huérfanas")
            self.stdout.write("   --test: Modo prueba (no elimina nada)")
            self.stdout.write("   --delete-public-id ID: Eliminar imagen específica")

    def _list_images(self):
        """Lista todas las imágenes en Cloudinary y su estado de uso"""
        self.stdout.write("\n📋 LISTADO DE IMÁGENES EN CLOUDINARY:")
        
        try:
            # Obtener imágenes de Cloudinary
            cloudinary_resources = cloudinary.api.resources(type="upload", max_results=500)
            
            # Obtener URLs en uso
            used_urls = set()
            
            # Carrusel
            carousel_images = CarouselImage.objects.all()
            for img in carousel_images:
                if img.imagen:
                    used_urls.add(str(img.imagen.url))
            
            # Servicios
            servicios = Servicio.objects.all()
            for servicio in servicios:
                if hasattr(servicio, 'imagen') and servicio.imagen:
                    used_urls.add(str(servicio.imagen.url))
            
            # Barberos  
            barberos = Barbero.objects.all()
            for barbero in barberos:
                if hasattr(barbero, 'imagen') and barbero.imagen:
                    used_urls.add(str(barbero.imagen.url))
            
            # Cursos
            cursos = Curso.objects.all()
            for curso in cursos:
                if hasattr(curso, 'imagen') and curso.imagen:
                    used_urls.add(str(curso.imagen.url))
            
            # Analizar cada imagen de Cloudinary
            used_count = 0
            orphaned_count = 0
            
            for resource in cloudinary_resources.get('resources', []):
                public_id = resource['public_id']
                secure_url = resource['secure_url']
                size = resource.get('bytes', 0)
                format_type = resource.get('format', 'unknown')
                
                is_used = secure_url in used_urls
                
                if is_used:
                    status = "✅ EN USO"
                    used_count += 1
                else:
                    status = "❌ HUÉRFANA"
                    orphaned_count += 1
                
                self.stdout.write(
                    f"  {status}: {public_id} ({format_type}, {size} bytes)"
                )
            
            # Resumen
            self.stdout.write(f"\n📊 RESUMEN:")
            self.stdout.write(f"  ✅ Imágenes en uso: {used_count}")
            self.stdout.write(f"  ❌ Imágenes huérfanas: {orphaned_count}")
            self.stdout.write(f"  📦 Total en Cloudinary: {len(cloudinary_resources.get('resources', []))}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error listando imágenes: {e}"))

    def _test_cleanup(self):
        """Simula la limpieza sin eliminar nada"""
        self.stdout.write("\n🧪 SIMULACIÓN DE LIMPIEZA:")
        
        try:
            cloudinary_resources = cloudinary.api.resources(type="upload", max_results=500)
            
            used_urls = set()
            
            # Recopilar URLs en uso (igual que en cleanup real)
            for carousel_img in CarouselImage.objects.all():
                if carousel_img.imagen:
                    used_urls.add(str(carousel_img.imagen.url))
            
            for servicio in Servicio.objects.all():
                if hasattr(servicio, 'imagen') and servicio.imagen:
                    used_urls.add(str(servicio.imagen.url))
            
            for barbero in Barbero.objects.all():
                if hasattr(barbero, 'imagen') and barbero.imagen:
                    used_urls.add(str(barbero.imagen.url))
            
            for curso in Curso.objects.all():
                if hasattr(curso, 'imagen') and curso.imagen:
                    used_urls.add(str(curso.imagen.url))
            
            # Simular eliminación
            would_delete = []
            for resource in cloudinary_resources.get('resources', []):
                if resource['secure_url'] not in used_urls:
                    would_delete.append(resource['public_id'])
            
            self.stdout.write(f"Se eliminarían {len(would_delete)} imágenes:")
            for public_id in would_delete[:10]:  # Mostrar solo las primeras 10
                self.stdout.write(f"  - {public_id}")
            
            if len(would_delete) > 10:
                self.stdout.write(f"  ... y {len(would_delete) - 10} más")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error en simulación: {e}"))
