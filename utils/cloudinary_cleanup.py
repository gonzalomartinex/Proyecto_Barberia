"""
Señales para limpiar automáticamente imágenes de Cloudinary cuando se eliminan objetos
"""

from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver
from BarberiaApp.models import CarouselImage
from servicios.models import Servicio
from usuarios.models import Barbero
from cursos.models import Curso
import cloudinary.uploader
import logging

logger = logging.getLogger(__name__)

def extract_public_id_from_url(image_url):
    """
    Extrae el public_id de una URL de Cloudinary para poder eliminarla
    
    Ejemplos de URLs de Cloudinary:
    - https://res.cloudinary.com/yourcloud/image/upload/v1234567890/folder/filename.jpg
    - https://res.cloudinary.com/yourcloud/image/upload/folder/filename.jpg
    """
    if not image_url:
        return None
        
    try:
        # Verificar que es una URL de Cloudinary
        if 'cloudinary.com' not in str(image_url):
            return None
            
        # Extraer la parte después de /upload/
        parts = str(image_url).split('/upload/')
        if len(parts) < 2:
            return None
            
        # Obtener la parte del path después de upload/
        path_part = parts[1]
        
        # Remover versión si existe (v1234567890/)
        if path_part.startswith('v') and '/' in path_part:
            # Buscar el primer slash después de la versión
            version_end = path_part.find('/')
            if version_end != -1:
                path_part = path_part[version_end + 1:]
        
        # Remover extensión del archivo
        if '.' in path_part:
            path_part = path_part.rsplit('.', 1)[0]
        
        return path_part
        
    except Exception as e:
        logger.warning(f"Error extrayendo public_id de {image_url}: {e}")
        return None

def delete_from_cloudinary(public_id):
    """
    Elimina una imagen de Cloudinary usando su public_id
    """
    if not public_id:
        return False
        
    try:
        result = cloudinary.uploader.destroy(public_id)
        
        if result.get('result') == 'ok':
            logger.info(f"✅ Imagen eliminada de Cloudinary: {public_id}")
            return True
        else:
            logger.warning(f"⚠️ Cloudinary no pudo eliminar: {public_id} - {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error eliminando de Cloudinary {public_id}: {e}")
        return False

@receiver(pre_delete, sender=CarouselImage)
def delete_carousel_image_from_cloudinary(sender, instance, **kwargs):
    """
    Elimina la imagen del carrusel de Cloudinary antes de eliminar el registro
    """
    if instance.imagen:
        public_id = extract_public_id_from_url(instance.imagen.url)
        if public_id:
            success = delete_from_cloudinary(public_id)
            if success:
                logger.info(f"🎠 Imagen de carrusel eliminada de Cloudinary: {instance.imagen.name}")
            else:
                logger.warning(f"⚠️ No se pudo eliminar imagen de carrusel de Cloudinary: {instance.imagen.name}")

@receiver(pre_delete, sender=Servicio)
def delete_servicio_image_from_cloudinary(sender, instance, **kwargs):
    """
    Elimina la imagen del servicio de Cloudinary antes de eliminar el registro
    """
    if hasattr(instance, 'imagen') and instance.imagen:
        public_id = extract_public_id_from_url(instance.imagen.url)
        if public_id:
            success = delete_from_cloudinary(public_id)
            if success:
                logger.info(f"🔧 Imagen de servicio eliminada de Cloudinary: {instance.nombre}")
            else:
                logger.warning(f"⚠️ No se pudo eliminar imagen de servicio de Cloudinary: {instance.nombre}")

@receiver(pre_delete, sender=Barbero)
def delete_barbero_image_from_cloudinary(sender, instance, **kwargs):
    """
    Elimina la imagen del barbero de Cloudinary antes de eliminar el registro
    """
    if hasattr(instance, 'imagen') and instance.imagen:
        public_id = extract_public_id_from_url(instance.imagen.url)
        if public_id:
            success = delete_from_cloudinary(public_id)
            if success:
                logger.info(f"✂️ Imagen de barbero eliminada de Cloudinary: {instance.nombre}")
            else:
                logger.warning(f"⚠️ No se pudo eliminar imagen de barbero de Cloudinary: {instance.nombre}")

@receiver(pre_delete, sender=Curso)
def delete_curso_image_from_cloudinary(sender, instance, **kwargs):
    """
    Elimina la imagen del curso de Cloudinary antes de eliminar el registro
    """
    if hasattr(instance, 'imagen') and instance.imagen:
        public_id = extract_public_id_from_url(instance.imagen.url)
        if public_id:
            success = delete_from_cloudinary(public_id)
            if success:
                logger.info(f"📚 Imagen de curso eliminada de Cloudinary: {instance.titulo}")
            else:
                logger.warning(f"⚠️ No se pudo eliminar imagen de curso de Cloudinary: {instance.titulo}")

# Función para limpiar imágenes huérfanas manualmente
def cleanup_orphaned_cloudinary_images():
    """
    Función utilitaria para limpiar imágenes huérfanas en Cloudinary
    (que ya no tienen registros asociados en la base de datos)
    
    Esta función se puede llamar manualmente o desde un comando de gestión
    """
    try:
        # Obtener todas las imágenes de Cloudinary
        cloudinary_resources = cloudinary.api.resources(type="upload", max_results=500)
        
        all_image_urls = set()
        
        # Recopilar todas las URLs de imágenes actualmente en uso
        for carousel_img in CarouselImage.objects.all():
            if carousel_img.imagen:
                all_image_urls.add(str(carousel_img.imagen.url))
        
        for servicio in Servicio.objects.all():
            if hasattr(servicio, 'imagen') and servicio.imagen:
                all_image_urls.add(str(servicio.imagen.url))
        
        for barbero in Barbero.objects.all():
            if hasattr(barbero, 'imagen') and barbero.imagen:
                all_image_urls.add(str(barbero.imagen.url))
        
        for curso in Curso.objects.all():
            if hasattr(curso, 'imagen') and curso.imagen:
                all_image_urls.add(str(curso.imagen.url))
        
        # Buscar imágenes huérfanas
        orphaned_count = 0
        for resource in cloudinary_resources.get('resources', []):
            resource_url = resource['secure_url']
            if resource_url not in all_image_urls:
                # Esta imagen no está siendo usada
                public_id = resource['public_id']
                success = delete_from_cloudinary(public_id)
                if success:
                    orphaned_count += 1
                    logger.info(f"🧹 Imagen huérfana eliminada: {public_id}")
        
        logger.info(f"🎉 Limpieza completada. {orphaned_count} imágenes huérfanas eliminadas.")
        return orphaned_count
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza de imágenes huérfanas: {e}")
        return 0
