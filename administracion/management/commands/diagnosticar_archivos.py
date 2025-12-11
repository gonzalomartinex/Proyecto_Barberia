from django.core.management.base import BaseCommand
from administracion.models import ArchivoExcel
from django.utils import timezone

class Command(BaseCommand):
    help = 'Diagnostica archivos Excel problemáticos'

    def handle(self, *args, **options):
        self.stdout.write("=== DIAGNÓSTICO DE ARCHIVOS EXCEL ===")
        total_archivos = ArchivoExcel.objects.count()
        self.stdout.write(f"Total de archivos en BD: {total_archivos}")

        if total_archivos == 0:
            self.stdout.write(self.style.ERROR("❌ No hay archivos Excel en la base de datos"))
            return

        self.stdout.write("")
        archivos_ok = 0
        archivos_sin_contenido = 0
        
        for i, archivo in enumerate(ArchivoExcel.objects.all().order_by('-fecha_creacion'), 1):
            self.stdout.write(f"{i}. {archivo.nombre_archivo}")
            self.stdout.write(f"   📅 Creado: {archivo.fecha_creacion}")
            
            try:
                if archivo.has_archivo_excel():
                    if archivo.archivo_excel:
                        size_mb = len(archivo.archivo_excel) / 1024 / 1024
                        self.stdout.write(self.style.SUCCESS(f"   ✅ Contenido OK: {size_mb:.2f} MB"))
                        archivos_ok += 1
                    else:
                        self.stdout.write(self.style.ERROR(f"   ❌ archivo_excel es None"))
                        archivos_sin_contenido += 1
                else:
                    self.stdout.write(self.style.ERROR(f"   ❌ has_archivo_excel() retorna False"))
                    archivos_sin_contenido += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ⚠️ Error: {e}"))
                archivos_sin_contenido += 1

        self.stdout.write("")
        self.stdout.write(f"✅ Archivos OK: {archivos_ok}")
        self.stdout.write(f"❌ Archivos problemáticos: {archivos_sin_contenido}")
        
        if archivos_sin_contenido > 0:
            self.stdout.write("")
            self.stdout.write("🔧 Archivos problemáticos detectados:")
            for archivo in ArchivoExcel.objects.all():
                if not archivo.has_archivo_excel():
                    self.stdout.write(f"   - {archivo.nombre_archivo}")
            
            self.stdout.write("")
            self.stdout.write("💡 Para limpiar archivos sin contenido, ejecuta:")
            self.stdout.write("   python manage.py shell -c \"from administracion.models import ArchivoExcel; print('Eliminando:', [a.nombre_archivo for a in ArchivoExcel.objects.all() if not a.has_archivo_excel()]); ArchivoExcel.objects.filter(archivo_excel__isnull=True).delete(); print('Listo!')\"")
