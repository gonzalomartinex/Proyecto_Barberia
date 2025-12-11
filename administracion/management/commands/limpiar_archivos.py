from django.core.management.base import BaseCommand
from administracion.models import ArchivoExcel
from django.utils import timezone
from django.db.models import Q

class Command(BaseCommand):
    help = 'Diagnostica y limpia archivos Excel problemáticos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Eliminar archivos sin contenido válido',
        )
        parser.add_argument(
            '--mostrar-contenido',
            action='store_true',
            help='Mostrar parte del contenido de cada archivo (debug)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== DIAGNÓSTICO DE ARCHIVOS EXCEL ==="))
        
        total_archivos = ArchivoExcel.objects.count()
        self.stdout.write(f"Total de archivos en BD: {total_archivos}")

        if total_archivos == 0:
            self.stdout.write(self.style.ERROR("❌ No hay archivos Excel en la base de datos"))
            return

        self.stdout.write("")
        
        archivos_ok = 0
        archivos_sin_contenido = 0
        archivos_problema = 0
        archivos_problematicos = []
        
        for archivo in ArchivoExcel.objects.all().order_by('-fecha_creacion'):
            self.stdout.write(f"📄 {archivo.nombre_archivo}")
            self.stdout.write(f"   📅 Creado: {archivo.fecha_creacion}")
            
            # Estado del archivo_excel field
            if not hasattr(archivo, 'archivo_excel') or archivo.archivo_excel is None:
                status = "❌ Campo archivo_excel es None"
                archivos_sin_contenido += 1
                archivos_problematicos.append(archivo)
            elif archivo.archivo_excel == '':
                status = "❌ Campo archivo_excel está vacío"
                archivos_sin_contenido += 1
                archivos_problematicos.append(archivo)
            else:
                length = len(archivo.archivo_excel)
                if length < 100:  # Un archivo Excel válido en base64 debería ser mucho más largo
                    status = f"⚠️ Contenido muy pequeño: {length} chars"
                    archivos_problema += 1
                    archivos_problematicos.append(archivo)
                else:
                    status = f"✅ OK: {length} chars"
                    archivos_ok += 1
            
            self.stdout.write(f"   {status}")
            
            # Verificar método has_archivo_excel
            try:
                tiene_archivo = archivo.has_archivo_excel()
                self.stdout.write(f"   📊 has_archivo_excel(): {tiene_archivo}")
            except Exception as e:
                self.stdout.write(f"   ⚠️ Error en has_archivo_excel(): {e}")
                archivos_problema += 1
            
            if options['mostrar_contenido'] and archivo.archivo_excel:
                preview = archivo.archivo_excel[:50] + "..." if len(archivo.archivo_excel) > 50 else archivo.archivo_excel
                self.stdout.write(f"   🔍 Preview: {preview}")
            
            self.stdout.write("")

        # Resumen
        self.stdout.write(self.style.SUCCESS("=== RESUMEN ==="))
        self.stdout.write(f"✅ Archivos OK: {archivos_ok}")
        self.stdout.write(f"❌ Archivos sin contenido: {archivos_sin_contenido}")
        self.stdout.write(f"⚠️ Archivos problemáticos: {archivos_problema}")
        
        if archivos_problematicos:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("🔧 ARCHIVOS PROBLEMÁTICOS:"))
            for archivo in archivos_problematicos:
                self.stdout.write(f"   - {archivo.nombre_archivo} (ID: {archivo.id})")
            
            if options['limpiar']:
                self.stdout.write("")
                self.stdout.write(self.style.WARNING("🗑️ ELIMINANDO ARCHIVOS PROBLEMÁTICOS..."))
                
                for archivo in archivos_problematicos:
                    self.stdout.write(f"   Eliminando: {archivo.nombre_archivo}")
                    archivo.delete()
                
                self.stdout.write(self.style.SUCCESS(f"✅ Eliminados {len(archivos_problematicos)} archivos problemáticos"))
            else:
                self.stdout.write("")
                self.stdout.write("💡 Para eliminar archivos problemáticos, ejecuta:")
                self.stdout.write("   python manage.py limpiar_archivos --limpiar")
                
        else:
            self.stdout.write(self.style.SUCCESS("🎉 Todos los archivos están en buen estado!"))
        
        # Información adicional
        self.stdout.write("")
        self.stdout.write("📋 INFORMACIÓN ADICIONAL:")
        self.stdout.write("   - Los archivos se almacenan como base64 en el campo 'archivo_excel'")
        self.stdout.write("   - Un archivo Excel válido debería tener >1000 caracteres en base64")
        self.stdout.write("   - Si aparecen archivos en la lista pero dan error 500, ejecuta --limpiar")
