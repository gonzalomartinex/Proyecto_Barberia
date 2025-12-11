from django.core.management.base import BaseCommand
from administracion.models import ArchivoExcel
from django.conf import settings
from pathlib import Path
import base64

class Command(BaseCommand):
    help = 'Repara archivos Excel que contienen solo nombres en lugar de contenido base64'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reparar',
            action='store_true',
            help='Reparar archivos problemáticos (buscar archivo local y convertir a base64)',
        )
        parser.add_argument(
            '--eliminar-huerfanos',
            action='store_true',
            help='Eliminar registros que no se pueden reparar',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== REPARACIÓN DE ARCHIVOS EXCEL PROBLEMÁTICOS ==="))
        
        archivos_problematicos = []
        archivos_reparados = 0
        archivos_eliminados = 0
        
        # Verificar cada archivo
        for archivo in ArchivoExcel.objects.all():
            try:
                # Intentar obtener bytes - esto fallará si solo tiene el nombre
                archivo.get_archivo_excel_bytes()
                self.stdout.write(f"✅ OK: {archivo.nombre_archivo}")
                
            except ValueError as e:
                self.stdout.write(f"❌ PROBLEMA: {archivo.nombre_archivo}")
                self.stdout.write(f"   Error: {e}")
                archivos_problematicos.append(archivo)
        
        if not archivos_problematicos:
            self.stdout.write(self.style.SUCCESS("🎉 Todos los archivos están en buen estado!"))
            return
        
        self.stdout.write(f"\n🔧 ARCHIVOS PROBLEMÁTICOS: {len(archivos_problematicos)}")
        
        if options['reparar']:
            # Intentar reparar archivos
            archivos_dir = Path(settings.MEDIA_ROOT) / 'archivos_turnos'
            
            for archivo in archivos_problematicos:
                archivo_local = archivos_dir / archivo.nombre_archivo
                
                if archivo_local.exists():
                    try:
                        # Leer archivo local y convertir a base64
                        with open(archivo_local, 'rb') as f:
                            archivo_bytes = f.read()
                            archivo_base64 = base64.b64encode(archivo_bytes).decode('utf-8')
                        
                        # Actualizar el registro
                        archivo.archivo_excel = archivo_base64
                        archivo.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ REPARADO: {archivo.nombre_archivo}")
                        )
                        archivos_reparados += 1
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"❌ Error reparando {archivo.nombre_archivo}: {e}")
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️ Archivo local no encontrado: {archivo_local}")
                    )
        
        if options['eliminar_huerfanos']:
            # Eliminar archivos que no se pudieron reparar
            for archivo in archivos_problematicos:
                archivo_local = Path(settings.MEDIA_ROOT) / 'archivos_turnos' / archivo.nombre_archivo
                
                if not archivo_local.exists() or not options['reparar']:
                    archivo.delete()
                    self.stdout.write(
                        self.style.WARNING(f"🗑️ ELIMINADO: {archivo.nombre_archivo} (huérfano)")
                    )
                    archivos_eliminados += 1
        
        # Resumen final
        self.stdout.write("\n=== RESUMEN ===")
        self.stdout.write(f"🔧 Archivos reparados: {archivos_reparados}")
        self.stdout.write(f"🗑️ Archivos eliminados: {archivos_eliminados}")
        
        if not options['reparar'] and not options['eliminar_huerfanos']:
            self.stdout.write("\n💡 OPCIONES DISPONIBLES:")
            self.stdout.write("   --reparar: Buscar archivos locales y convertir a base64")
            self.stdout.write("   --eliminar-huerfanos: Eliminar registros sin archivo local")
            self.stdout.write("\n🚀 EJEMPLO DE USO:")
            self.stdout.write("   python manage.py reparar_archivos --reparar --eliminar-huerfanos")
