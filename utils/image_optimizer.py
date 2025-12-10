"""
Sistema de optimización y conversión de imágenes local
Reemplaza la dependencia de Cloudinary con manejo local optimizado
"""
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import uuid
from io import BytesIO

# Importación lazy de PIL para evitar problemas de carga en el deploy
try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageOps = None


class ImageOptimizer:
    """
    Optimizador de imágenes que convierte automáticamente a WebP
    y redimensiona según el contexto de uso
    """
    
    # Configuraciones por tipo de imagen
    SIZES = {
        'perfil': {'width': 400, 'height': 400, 'quality': 85},
        'producto': {'width': 800, 'height': 600, 'quality': 80},
        'barbero': {'width': 600, 'height': 600, 'quality': 85},
        'servicio': {'width': 800, 'height': 500, 'quality': 80},
        'curso': {'width': 1000, 'height': 600, 'quality': 80},
        'default': {'width': 800, 'height': 600, 'quality': 80}
    }
    
    ALLOWED_FORMATS = ['JPEG', 'PNG', 'WEBP', 'BMP', 'TIFF']
    
    @classmethod
    def optimize_image(cls, image_file, image_type='default', maintain_aspect=True):
        """
        Optimiza una imagen: convierte a WebP, redimensiona y comprime
        
        Args:
            image_file: Archivo de imagen Django
            image_type: Tipo de imagen ('perfil', 'producto', etc.)
            maintain_aspect: Mantener proporción de aspecto
            
        Returns:
            ContentFile: Archivo optimizado listo para guardar
        """
        if not PIL_AVAILABLE:
            # Si PIL no está disponible, devolver el archivo original
            return image_file
            
        try:
            # Obtener configuración para el tipo de imagen
            config = cls.SIZES.get(image_type, cls.SIZES['default'])
            
            # Abrir imagen con PIL
            with Image.open(image_file) as img:
                # Verificar formato
                if img.format not in cls.ALLOWED_FORMATS:
                    raise ValueError(f"Formato {img.format} no soportado")
                
                # Convertir a RGB si es necesario (para WebP)
                if img.mode in ('RGBA', 'P'):
                    # Crear fondo blanco para transparencias
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if 'transparency' in img.info else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Corregir orientación EXIF
                img = ImageOps.exif_transpose(img)
                
                # Redimensionar manteniendo aspecto si se especifica
                if maintain_aspect:
                    img.thumbnail((config['width'], config['height']), Image.Resampling.LANCZOS)
                else:
                    img = img.resize((config['width'], config['height']), Image.Resampling.LANCZOS)
                
                # Aplicar sharpening suave
                from PIL import ImageFilter
                img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
                
                # Convertir a WebP
                output = BytesIO()
                img.save(
                    output,
                    format='WEBP',
                    quality=config['quality'],
                    optimize=True,
                    method=6  # Mejor compresión
                )
                output.seek(0)
                
                # Generar nombre único
                filename = f"{uuid.uuid4().hex}.webp"
                
                return ContentFile(output.getvalue(), name=filename)
                
        except Exception as e:
            print(f"Error optimizando imagen: {e}")
            raise
    
    @classmethod
    def get_optimized_path(cls, original_path, image_type='default'):
        """
        Genera la ruta optimizada para una imagen
        """
        base_name = os.path.splitext(os.path.basename(original_path))[0]
        return f"{image_type}/{base_name}_{uuid.uuid4().hex[:8]}.webp"
    
    @classmethod
    def create_multiple_sizes(cls, image_file, base_name, sizes=['small', 'medium', 'large']):
        """
        Crea múltiples tamaños de una imagen
        
        Returns:
            dict: Diccionario con los ContentFiles de cada tamaño
        """
        size_configs = {
            'small': {'width': 300, 'height': 200, 'quality': 80},
            'medium': {'width': 600, 'height': 400, 'quality': 85},
            'large': {'width': 1200, 'height': 800, 'quality': 90}
        }
        
        results = {}
        
        for size in sizes:
            if size in size_configs:
                config = size_configs[size]
                # Temporarily override the size config
                original_config = cls.SIZES.get('default')
                cls.SIZES['temp'] = config
                
                try:
                    optimized = cls.optimize_image(image_file, 'temp')
                    results[size] = optimized
                except Exception as e:
                    print(f"Error creando tamaño {size}: {e}")
                    continue
        
        return results


def optimize_and_save(image_field, image_file, image_type='default'):
    """
    Función helper para optimizar y guardar una imagen en un campo modelo
    
    Args:
        image_field: Campo ImageField del modelo
        image_file: Archivo de imagen subido
        image_type: Tipo de imagen para optimización
        
    Returns:
        str: Ruta del archivo guardado
    """
    try:
        # Optimizar imagen
        optimized_file = ImageOptimizer.optimize_image(image_file, image_type)
        
        # Generar ruta
        upload_path = f"{image_type}s/{optimized_file.name}"
        
        # Guardar archivo optimizado
        saved_path = image_field.storage.save(upload_path, optimized_file)
        
        return saved_path
        
    except Exception as e:
        print(f"Error en optimize_and_save: {e}")
        raise


class LocalImageStorage:
    """
    Manejador de almacenamiento local de imágenes optimizado
    """
    
    @staticmethod
    def get_media_path(relative_path):
        """Obtiene la ruta completa de un archivo media"""
        return os.path.join(settings.MEDIA_ROOT, relative_path)
    
    @staticmethod
    def get_media_url(relative_path):
        """Obtiene la URL de un archivo media"""
        if not relative_path:
            return ""
        return f"{settings.MEDIA_URL}{relative_path}"
    
    @staticmethod
    def ensure_media_dirs():
        """Asegura que existan los directorios necesarios"""
        base_dirs = ['perfiles', 'productos', 'barberos', 'servicios', 'cursos']
        
        for dir_name in base_dirs:
            dir_path = os.path.join(settings.MEDIA_ROOT, dir_name)
            os.makedirs(dir_path, exist_ok=True)
    
    @staticmethod
    def cleanup_old_files(keep_days=30):
        """Limpia archivos antiguos no utilizados"""
        # Esta función puede implementarse para limpiar archivos huérfanos
        pass
