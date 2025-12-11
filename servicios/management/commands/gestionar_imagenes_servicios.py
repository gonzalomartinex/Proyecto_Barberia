from django.core.management.base import BaseCommand
from servicios.models import Servicio
from utils.cloudinary_cleanup import extract_public_id_from_url, delete_from_cloudinary
import cloudinary.api
from django.contrib import messages

class Command(BaseCommand):
    help = 'Gestiona imágenes de servicios en Cloudinary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--listar',
            action='store_true',
            help='Listar todos los servicios y estado de sus imágenes',
        )
        parser.add_argument(
            '--verificar-huerfanas',
            action='store_true',
            help='Buscar imágenes de servicios huérfanas en Cloudinary',
        )
        parser.add_argument(
            '--limpiar-huerfanas',
            action='store_true',
            help='Eliminar imágenes de servicios huérfanas de Cloudinary',
        )
        parser.add_argument(
            '--servicio-id',
            type=int,
            help='ID específico de servicio para operar',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== GESTIÓN DE IMÁGENES DE SERVICIOS ==="))
        
        if options['listar']:
            self._listar_servicios()
        
        if options['verificar_huerfanas']:
            huerfanas = self._encontrar_huerfanas()
            if huerfanas:
                self.stdout.write(f"\n❌ Se encontraron {len(huerfanas)} imágenes huérfanas de servicios:")
                for public_id in huerfanas[:5]:  # Mostrar solo las primeras 5
                    self.stdout.write(f"   - {public_id}")
                if len(huerfanas) > 5:
                    self.stdout.write(f"   ... y {len(huerfanas) - 5} más")
            else:
                self.stdout.write("\n✅ No se encontraron imágenes huérfanas de servicios")
        
        if options['limpiar_huerfanas']:
            huerfanas = self._encontrar_huerfanas()
            if huerfanas:
                self.stdout.write(f"\n🧹 Limpiando {len(huerfanas)} imágenes huérfanas de servicios...")
                eliminadas = 0
                for public_id in huerfanas:
                    if delete_from_cloudinary(public_id):
                        eliminadas += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ {eliminadas} imágenes huérfanas eliminadas")
                )
            else:
                self.stdout.write("\n✅ No hay imágenes huérfanas para limpiar")
        
        if options['servicio_id']:
            self._analizar_servicio_especifico(options['servicio_id'])

    def _listar_servicios(self):
        """Lista todos los servicios y el estado de sus imágenes"""
        self.stdout.write("\n📋 SERVICIOS Y SUS IMÁGENES:")
        
        servicios = Servicio.objects.all().order_by('orden', 'nombre')
        
        servicios_con_imagen = 0
        servicios_sin_imagen = 0
        
        for servicio in servicios:
            if servicio.imagen:
                try:
                    public_id = extract_public_id_from_url(servicio.imagen.url)
                    if public_id and 'cloudinary.com' in str(servicio.imagen.url):
                        status = "✅ CLOUDINARY"
                        servicios_con_imagen += 1
                    else:
                        status = "📁 LOCAL"
                        servicios_con_imagen += 1
                except:
                    status = "❓ DESCONOCIDO"
                    servicios_con_imagen += 1
                    
                self.stdout.write(
                    f"  {status}: {servicio.nombre} (ID: {servicio.id}) - ${servicio.precio}"
                )
                if public_id:
                    self.stdout.write(f"    🔗 Public ID: {public_id}")
            else:
                self.stdout.write(
                    f"  ❌ SIN IMAGEN: {servicio.nombre} (ID: {servicio.id}) - ${servicio.precio}"
                )
                servicios_sin_imagen += 1
        
        # Resumen
        total = servicios.count()
        self.stdout.write(f"\n📊 RESUMEN:")
        self.stdout.write(f"  📦 Total servicios: {total}")
        self.stdout.write(f"  🖼️  Con imagen: {servicios_con_imagen}")
        self.stdout.write(f"  ❌ Sin imagen: {servicios_sin_imagen}")

    def _encontrar_huerfanas(self):
        """Encuentra imágenes de servicios huérfanas en Cloudinary"""
        try:
            # Obtener todas las imágenes de Cloudinary con prefijo 'servicios'
            cloudinary_resources = cloudinary.api.resources(
                type="upload", 
                prefix="servicios/",  # Asumiendo que las imágenes de servicios usan este prefijo
                max_results=500
            )
            
            # Obtener public_ids de servicios en uso
            servicios_public_ids = set()
            for servicio in Servicio.objects.all():
                if servicio.imagen:
                    public_id = extract_public_id_from_url(servicio.imagen.url)
                    if public_id:
                        servicios_public_ids.add(public_id)
            
            # Encontrar huérfanas
            huerfanas = []
            for resource in cloudinary_resources.get('resources', []):
                public_id = resource['public_id']
                if public_id not in servicios_public_ids:
                    huerfanas.append(public_id)
            
            return huerfanas
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error buscando huérfanas: {e}"))
            return []

    def _analizar_servicio_especifico(self, servicio_id):
        """Analiza un servicio específico en detalle"""
        try:
            servicio = Servicio.objects.get(id=servicio_id)
            self.stdout.write(f"\n🔍 ANÁLISIS DETALLADO DEL SERVICIO:")
            self.stdout.write(f"  📛 Nombre: {servicio.nombre}")
            self.stdout.write(f"  💰 Precio: ${servicio.precio}")
            self.stdout.write(f"  📊 Orden: {servicio.orden}")
            
            if servicio.imagen:
                self.stdout.write(f"  🖼️  URL imagen: {servicio.imagen.url}")
                
                public_id = extract_public_id_from_url(servicio.imagen.url)
                if public_id:
                    self.stdout.write(f"  🔗 Public ID: {public_id}")
                    
                    # Verificar si existe en Cloudinary
                    try:
                        resource = cloudinary.api.resource(public_id)
                        self.stdout.write(f"  ✅ Estado en Cloudinary: EXISTE")
                        self.stdout.write(f"     - Formato: {resource.get('format', 'desconocido')}")
                        self.stdout.write(f"     - Tamaño: {resource.get('bytes', 0)} bytes")
                        self.stdout.write(f"     - Dimensiones: {resource.get('width', '?')}x{resource.get('height', '?')}")
                    except:
                        self.stdout.write(f"  ❌ Estado en Cloudinary: NO EXISTE")
                else:
                    self.stdout.write(f"  ⚠️  No se pudo extraer public_id (puede ser imagen local)")
            else:
                self.stdout.write(f"  ❌ Sin imagen")
                
        except Servicio.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Servicio con ID {servicio_id} no encontrado"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error analizando servicio: {e}"))
