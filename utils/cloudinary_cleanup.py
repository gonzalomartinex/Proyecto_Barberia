"""
Utilidades para limpiar automáticamente imágenes de Cloudinary
"""

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

# Funciones utilitarias - las señales están definidas en cada modelo respectivo

def obtener_imagenes_cloudinary(folder_prefix=""):
    """
    Obtiene una lista de todas las imágenes en Cloudinary
    
    Args:
        folder_prefix (str): Prefijo de carpeta para filtrar (ej: "productos/")
    
    Returns:
        list: Lista de nombres de archivos/paths de imágenes
    """
    try:
        import cloudinary.api
        
        imagenes = []
        next_cursor = None
        
        while True:
            if folder_prefix:
                result = cloudinary.api.resources(
                    type="upload",
                    prefix=folder_prefix,
                    max_results=100,
                    next_cursor=next_cursor
                )
            else:
                result = cloudinary.api.resources(
                    type="upload",
                    max_results=100,
                    next_cursor=next_cursor
                )
            
            for resource in result.get('resources', []):
                imagenes.append(resource['public_id'])
            
            next_cursor = result.get('next_cursor')
            if not next_cursor:
                break
        
        return imagenes
        
    except Exception as e:
        logger.error(f"Error al obtener imágenes de Cloudinary: {str(e)}")
        return []

def existe_imagen_cloudinary(public_id):
    """
    Verifica si una imagen existe en Cloudinary
    
    Args:
        public_id (str): El public_id de la imagen en Cloudinary
    
    Returns:
        bool: True si existe, False si no existe
    """
    try:
        import cloudinary.api
        cloudinary.api.resource(public_id)
        return True
    except cloudinary.api.NotFound:
        return False
    except Exception as e:
        logger.error(f"Error al verificar imagen en Cloudinary: {str(e)}")
        return False

def eliminar_imagen_cloudinary(image_field):
    """
    Elimina una imagen de Cloudinary usando el campo de imagen de Django
    
    Args:
        image_field: Campo ImageField/FileField de Django
    
    Returns:
        bool: True si se eliminó exitosamente, False si hubo error
    """
    if not image_field:
        return False
        
    try:
        # Obtener la URL de la imagen
        if hasattr(image_field, 'url'):
            image_url = image_field.url
        else:
            image_url = str(image_field)
        
        # Extraer el public_id
        public_id = extract_public_id_from_url(image_url)
        if public_id:
            return delete_from_cloudinary(public_id)
        else:
            logger.warning(f"No se pudo extraer public_id de: {image_url}")
            return False
            
    except Exception as e:
        logger.error(f"Error al eliminar imagen de Cloudinary: {str(e)}")
        return False
