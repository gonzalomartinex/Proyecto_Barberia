from django.core.management.base import BaseCommand
from usuarios.models import Barbero, TrabajoBarbero
from utils.cloudinary_cleanup import extract_public_id_from_url, delete_from_cloudinary
import cloudinary.api

class Command(BaseCommand):
    help = 'Gestiona imágenes de barberos y sus trabajos en Cloudinary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--listar',
            action='store_true',
            help='Listar todos los barberos y estado de sus imágenes',
        )
        parser.add_argument(
            '--verificar-huerfanas',
            action='store_true',
            help='Buscar imágenes de barberos huérfanas en Cloudinary',
        )
        parser.add_argument(
            '--limpiar-huerfanas',
            action='store_true',
            help='Eliminar imágenes de barberos huérfanas de Cloudinary',
        )
        parser.add_argument(
            '--barbero-id',
            type=int,
            help='ID específico de barbero para operar',
        )
        parser.add_argument(
            '--solo-trabajos',
            action='store_true',
            help='Operar solo con trabajos de barberos (no fotos de perfil)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== GESTIÓN DE IMÁGENES DE BARBEROS ==="))
        
        if options['listar']:
            self._listar_barberos()
        
        if options['verificar_huerfanas']:
            huerfanas_fotos, huerfanas_trabajos = self._encontrar_huerfanas()
            total = len(huerfanas_fotos) + len(huerfanas_trabajos)
            
            if total > 0:
                self.stdout.write(f"\n❌ Se encontraron {total} imágenes huérfanas de barberos:")
                if huerfanas_fotos:
                    self.stdout.write(f"   👤 Fotos de perfil: {len(huerfanas_fotos)}")
                    for public_id in huerfanas_fotos[:3]:
                        self.stdout.write(f"      - {public_id}")
                    if len(huerfanas_fotos) > 3:
                        self.stdout.write(f"      ... y {len(huerfanas_fotos) - 3} más")
                
                if huerfanas_trabajos:
                    self.stdout.write(f"   🎨 Trabajos: {len(huerfanas_trabajos)}")
                    for public_id in huerfanas_trabajos[:3]:
                        self.stdout.write(f"      - {public_id}")
                    if len(huerfanas_trabajos) > 3:
                        self.stdout.write(f"      ... y {len(huerfanas_trabajos) - 3} más")
            else:
                self.stdout.write("\n✅ No se encontraron imágenes huérfanas de barberos")
        
        if options['limpiar_huerfanas']:
            huerfanas_fotos, huerfanas_trabajos = self._encontrar_huerfanas()
            total_eliminadas = 0
            
            if huerfanas_fotos:
                self.stdout.write(f"\n🧹 Limpiando {len(huerfanas_fotos)} fotos de perfil huérfanas...")
                for public_id in huerfanas_fotos:
                    if delete_from_cloudinary(public_id):
                        total_eliminadas += 1
            
            if huerfanas_trabajos:
                self.stdout.write(f"🧹 Limpiando {len(huerfanas_trabajos)} trabajos huérfanos...")
                for public_id in huerfanas_trabajos:
                    if delete_from_cloudinary(public_id):
                        total_eliminadas += 1
            
            if total_eliminadas > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ {total_eliminadas} imágenes huérfanas eliminadas")
                )
            else:
                self.stdout.write("✅ No hay imágenes huérfanas para limpiar")
        
        if options['barbero_id']:
            self._analizar_barbero_especifico(options['barbero_id'])

    def _listar_barberos(self):
        """Lista todos los barberos y el estado de sus imágenes"""
        self.stdout.write("\n👥 BARBEROS Y SUS IMÁGENES:")
        
        barberos = Barbero.objects.all().order_by('orden', 'nombre')
        
        barberos_con_foto = 0
        barberos_sin_foto = 0
        total_trabajos = 0
        
        for barbero in barberos:
            trabajos_count = barbero.trabajos.filter(imagen__isnull=False).count()
            total_trabajos += trabajos_count
            
            # Status de foto de perfil
            if barbero.foto:
                try:
                    public_id = extract_public_id_from_url(barbero.foto.url)
                    if public_id and 'cloudinary.com' in str(barbero.foto.url):
                        foto_status = "✅ CLOUDINARY"
                    else:
                        foto_status = "📁 LOCAL"
                    barberos_con_foto += 1
                except:
                    foto_status = "❓ DESCONOCIDO"
                    barberos_con_foto += 1
            else:
                foto_status = "❌ SIN FOTO"
                barberos_sin_foto += 1
            
            self.stdout.write(
                f"  {foto_status}: {barbero.nombre} (ID: {barbero.id})"
            )
            
            if trabajos_count > 0:
                self.stdout.write(f"    🎨 Trabajos: {trabajos_count}")
                # Mostrar algunos public_ids de trabajos
                for trabajo in barbero.trabajos.filter(imagen__isnull=False)[:2]:
                    public_id = extract_public_id_from_url(trabajo.imagen.url)
                    if public_id:
                        self.stdout.write(f"       - {public_id}")
                if trabajos_count > 2:
                    self.stdout.write(f"       ... y {trabajos_count - 2} más")
            else:
                self.stdout.write(f"    🎨 Sin trabajos")
        
        # Resumen
        total = barberos.count()
        self.stdout.write(f"\n📊 RESUMEN:")
        self.stdout.write(f"  👤 Total barberos: {total}")
        self.stdout.write(f"  📷 Con foto: {barberos_con_foto}")
        self.stdout.write(f"  ❌ Sin foto: {barberos_sin_foto}")
        self.stdout.write(f"  🎨 Total trabajos: {total_trabajos}")

    def _encontrar_huerfanas(self):
        """Encuentra imágenes de barberos huérfanas en Cloudinary"""
        try:
            # Obtener imágenes de barberos (fotos de perfil)
            barberos_resources = []
            try:
                barberos_resources = cloudinary.api.resources(
                    type="upload", 
                    prefix="barberos/",  # Asumiendo prefijo para barberos
                    max_results=500
                ).get('resources', [])
            except:
                pass
            
            # Obtener imágenes de trabajos
            trabajos_resources = []
            try:
                trabajos_resources = cloudinary.api.resources(
                    type="upload", 
                    prefix="trabajos/",  # Asumiendo prefijo para trabajos
                    max_results=500
                ).get('resources', [])
            except:
                pass
            
            # También buscar sin prefijo específico
            try:
                general_resources = cloudinary.api.resources(
                    type="upload", 
                    max_results=1000
                ).get('resources', [])
                
                # Filtrar que parezcan ser de barberos
                for resource in general_resources:
                    public_id = resource['public_id'].lower()
                    if any(keyword in public_id for keyword in ['barbero', 'trabajo', 'corte', 'peluque']):
                        if 'barbero' in public_id or 'perfil' in public_id:
                            barberos_resources.append(resource)
                        elif 'trabajo' in public_id or 'corte' in public_id:
                            trabajos_resources.append(resource)
            except:
                pass
            
            # Obtener public_ids en uso
            fotos_en_uso = set()
            trabajos_en_uso = set()
            
            for barbero in Barbero.objects.all():
                if barbero.foto:
                    public_id = extract_public_id_from_url(barbero.foto.url)
                    if public_id:
                        fotos_en_uso.add(public_id)
                
                for trabajo in barbero.trabajos.all():
                    if trabajo.imagen:
                        public_id = extract_public_id_from_url(trabajo.imagen.url)
                        if public_id:
                            trabajos_en_uso.add(public_id)
            
            # Encontrar huérfanas
            huerfanas_fotos = []
            huerfanas_trabajos = []
            
            for resource in barberos_resources:
                public_id = resource['public_id']
                if public_id not in fotos_en_uso:
                    huerfanas_fotos.append(public_id)
            
            for resource in trabajos_resources:
                public_id = resource['public_id']
                if public_id not in trabajos_en_uso:
                    huerfanas_trabajos.append(public_id)
            
            return huerfanas_fotos, huerfanas_trabajos
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error buscando huérfanas: {e}"))
            return [], []

    def _analizar_barbero_especifico(self, barbero_id):
        """Analiza un barbero específico en detalle"""
        try:
            barbero = Barbero.objects.get(id=barbero_id)
            self.stdout.write(f"\n🔍 ANÁLISIS DETALLADO DEL BARBERO:")
            self.stdout.write(f"  👤 Nombre: {barbero.nombre}")
            self.stdout.write(f"  📞 Teléfono: {barbero.telefono}")
            self.stdout.write(f"  📊 Orden: {barbero.orden}")
            
            # Analizar foto de perfil
            if barbero.foto:
                self.stdout.write(f"  📷 URL foto: {barbero.foto.url}")
                
                public_id = extract_public_id_from_url(barbero.foto.url)
                if public_id:
                    self.stdout.write(f"  🔗 Public ID foto: {public_id}")
                    
                    try:
                        resource = cloudinary.api.resource(public_id)
                        self.stdout.write(f"  ✅ Estado en Cloudinary: EXISTE")
                        self.stdout.write(f"     - Formato: {resource.get('format', 'desconocido')}")
                        self.stdout.write(f"     - Tamaño: {resource.get('bytes', 0)} bytes")
                        self.stdout.write(f"     - Dimensiones: {resource.get('width', '?')}x{resource.get('height', '?')}")
                    except:
                        self.stdout.write(f"  ❌ Estado en Cloudinary: NO EXISTE")
                else:
                    self.stdout.write(f"  ⚠️  No se pudo extraer public_id (imagen local)")
            else:
                self.stdout.write(f"  ❌ Sin foto de perfil")
            
            # Analizar trabajos
            trabajos = barbero.trabajos.all()
            self.stdout.write(f"\n  🎨 TRABAJOS: {trabajos.count()}")
            
            for i, trabajo in enumerate(trabajos, 1):
                self.stdout.write(f"    {i}. Fecha: {trabajo.fecha.strftime('%Y-%m-%d %H:%M')}")
                if trabajo.imagen:
                    self.stdout.write(f"       URL: {trabajo.imagen.url}")
                    
                    public_id = extract_public_id_from_url(trabajo.imagen.url)
                    if public_id:
                        self.stdout.write(f"       Public ID: {public_id}")
                        try:
                            resource = cloudinary.api.resource(public_id)
                            self.stdout.write(f"       ✅ En Cloudinary: SÍ ({resource.get('format', '?')}, {resource.get('bytes', 0)} bytes)")
                        except:
                            self.stdout.write(f"       ❌ En Cloudinary: NO")
                    else:
                        self.stdout.write(f"       ⚠️  Imagen local")
                else:
                    self.stdout.write(f"       ❌ Sin imagen")
                
        except Barbero.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Barbero con ID {barbero_id} no encontrado"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error analizando barbero: {e}"))
