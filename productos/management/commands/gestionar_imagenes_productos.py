from django.core.management.base import BaseCommand
from django.conf import settings
from productos.models import Producto
from utils.cloudinary_cleanup import obtener_imagenes_cloudinary, eliminar_imagen_cloudinary
import cloudinary.api
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Gestiona las imágenes de productos en Cloudinary: auditoria, limpieza de huérfanas y verificación'

    def add_arguments(self, parser):
        parser.add_argument(
            '--accion',
            choices=['auditar', 'limpiar_huerfanas', 'verificar'],
            default='auditar',
            help='Acción a realizar: auditar (por defecto), limpiar_huerfanas, verificar'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra lo que se haría sin ejecutar cambios'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada'
        )

    def handle(self, *args, **options):
        accion = options['accion']
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        if accion == 'auditar':
            self.auditar_imagenes_productos(verbose)
        elif accion == 'limpiar_huerfanas':
            self.limpiar_imagenes_huerfanas_productos(dry_run, verbose)
        elif accion == 'verificar':
            self.verificar_imagenes_productos(verbose)

    def auditar_imagenes_productos(self, verbose=False):
        """Realiza una auditoría completa de las imágenes de productos"""
        self.stdout.write(self.style.SUCCESS('\n=== AUDITORÍA DE IMÁGENES DE PRODUCTOS ==='))
        
        # Obtener estadísticas básicas
        total_productos = Producto.objects.count()
        productos_con_imagen = Producto.objects.exclude(imagen__isnull=True).exclude(imagen__exact='').count()
        productos_sin_imagen = total_productos - productos_con_imagen
        
        self.stdout.write(f'📊 Total de productos: {total_productos}')
        self.stdout.write(f'🖼️  Productos con imagen: {productos_con_imagen}')
        self.stdout.write(f'❌ Productos sin imagen: {productos_sin_imagen}')
        
        # Obtener imágenes de Cloudinary en la carpeta de productos
        try:
            cloudinary_images = obtener_imagenes_cloudinary('productos/')
            self.stdout.write(f'☁️  Imágenes en Cloudinary (carpeta productos/): {len(cloudinary_images)}')
            
            if verbose and cloudinary_images:
                self.stdout.write('\n📋 Imágenes en Cloudinary:')
                for img in cloudinary_images[:10]:  # Mostrar solo las primeras 10
                    self.stdout.write(f'  - {img}')
                if len(cloudinary_images) > 10:
                    self.stdout.write(f'  ... y {len(cloudinary_images) - 10} más')
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al obtener imágenes de Cloudinary: {str(e)}'))
            cloudinary_images = []
        
        # Verificar imágenes huérfanas y faltantes
        imagenes_bd = []
        imagenes_faltantes = []
        
        for producto in Producto.objects.exclude(imagen__isnull=True).exclude(imagen__exact=''):
            imagen_path = producto.imagen.name
            imagenes_bd.append(imagen_path)
            
            # Verificar si la imagen existe en Cloudinary
            if imagen_path not in cloudinary_images:
                imagenes_faltantes.append({
                    'producto': producto.nombre,
                    'imagen': imagen_path
                })
        
        # Encontrar imágenes huérfanas en Cloudinary
        imagenes_huerfanas = [img for img in cloudinary_images if img not in imagenes_bd]
        
        self.stdout.write(f'🔍 Imágenes referenciadas en BD: {len(imagenes_bd)}')
        self.stdout.write(f'⚠️  Imágenes faltantes en Cloudinary: {len(imagenes_faltantes)}')
        self.stdout.write(f'🗑️  Imágenes huérfanas en Cloudinary: {len(imagenes_huerfanas)}')
        
        if verbose:
            if imagenes_faltantes:
                self.stdout.write('\n❌ Imágenes faltantes en Cloudinary:')
                for img in imagenes_faltantes:
                    self.stdout.write(f'  - Producto: {img["producto"]} | Imagen: {img["imagen"]}')
            
            if imagenes_huerfanas:
                self.stdout.write('\n🗑️  Imágenes huérfanas en Cloudinary:')
                for img in imagenes_huerfanas[:10]:  # Mostrar solo las primeras 10
                    self.stdout.write(f'  - {img}')
                if len(imagenes_huerfanas) > 10:
                    self.stdout.write(f'  ... y {len(imagenes_huerfanas) - 10} más')
        
        # Resumen final
        self.stdout.write('\n' + '='*50)
        if imagenes_faltantes or imagenes_huerfanas:
            self.stdout.write(self.style.WARNING('⚠️  Se encontraron inconsistencias'))
            if imagenes_huerfanas:
                self.stdout.write('💡 Usa --accion limpiar_huerfanas para eliminar imágenes huérfanas')
        else:
            self.stdout.write(self.style.SUCCESS('✅ Todas las imágenes están sincronizadas'))

    def limpiar_imagenes_huerfanas_productos(self, dry_run=False, verbose=False):
        """Elimina imágenes huérfanas de productos en Cloudinary"""
        action_text = "SIMULACIÓN" if dry_run else "LIMPIEZA"
        self.stdout.write(self.style.WARNING(f'\n=== {action_text} DE IMÁGENES HUÉRFANAS DE PRODUCTOS ==='))
        
        try:
            # Obtener imágenes de Cloudinary
            cloudinary_images = obtener_imagenes_cloudinary('productos/')
            
            # Obtener imágenes referenciadas en la BD
            imagenes_bd = []
            for producto in Producto.objects.exclude(imagen__isnull=True).exclude(imagen__exact=''):
                imagenes_bd.append(producto.imagen.name)
            
            # Encontrar huérfanas
            imagenes_huerfanas = [img for img in cloudinary_images if img not in imagenes_bd]
            
            if not imagenes_huerfanas:
                self.stdout.write(self.style.SUCCESS('✅ No se encontraron imágenes huérfanas de productos'))
                return
            
            self.stdout.write(f'🗑️  Encontradas {len(imagenes_huerfanas)} imágenes huérfanas')
            
            eliminadas = 0
            errores = 0
            
            for imagen in imagenes_huerfanas:
                if dry_run:
                    self.stdout.write(f'🔍 Se eliminaría: {imagen}')
                else:
                    try:
                        if eliminar_imagen_cloudinary(imagen):
                            eliminadas += 1
                            if verbose:
                                self.stdout.write(f'✅ Eliminada: {imagen}')
                        else:
                            errores += 1
                            if verbose:
                                self.stdout.write(f'❌ Error al eliminar: {imagen}')
                    except Exception as e:
                        errores += 1
                        if verbose:
                            self.stdout.write(f'❌ Error al eliminar {imagen}: {str(e)}')
            
            if dry_run:
                self.stdout.write(f'\n📋 Se eliminarían {len(imagenes_huerfanas)} imágenes huérfanas')
            else:
                self.stdout.write(f'\n✅ Eliminadas: {eliminadas}')
                if errores > 0:
                    self.stdout.write(self.style.ERROR(f'❌ Errores: {errores}'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error durante la limpieza: {str(e)}'))

    def verificar_imagenes_productos(self, verbose=False):
        """Verifica que todas las imágenes de productos existan en Cloudinary"""
        self.stdout.write(self.style.SUCCESS('\n=== VERIFICACIÓN DE IMÁGENES DE PRODUCTOS ==='))
        
        productos_con_imagen = Producto.objects.exclude(imagen__isnull=True).exclude(imagen__exact='')
        
        if not productos_con_imagen.exists():
            self.stdout.write('ℹ️  No hay productos con imágenes para verificar')
            return
        
        try:
            cloudinary_images = obtener_imagenes_cloudinary('productos/')
            
            imagenes_ok = 0
            imagenes_faltantes = 0
            
            for producto in productos_con_imagen:
                imagen_path = producto.imagen.name
                
                if imagen_path in cloudinary_images:
                    imagenes_ok += 1
                    if verbose:
                        self.stdout.write(f'✅ {producto.nombre}: {imagen_path}')
                else:
                    imagenes_faltantes += 1
                    self.stdout.write(self.style.ERROR(f'❌ FALTA - {producto.nombre}: {imagen_path}'))
            
            self.stdout.write(f'\n📊 Imágenes verificadas: {imagenes_ok + imagenes_faltantes}')
            self.stdout.write(f'✅ Imágenes encontradas: {imagenes_ok}')
            
            if imagenes_faltantes > 0:
                self.stdout.write(self.style.ERROR(f'❌ Imágenes faltantes: {imagenes_faltantes}'))
                self.stdout.write('💡 Las imágenes faltantes pueden haberse subido con nombres diferentes o estar en otra carpeta')
            else:
                self.stdout.write(self.style.SUCCESS('🎉 Todas las imágenes de productos están disponibles en Cloudinary'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error durante la verificación: {str(e)}'))
