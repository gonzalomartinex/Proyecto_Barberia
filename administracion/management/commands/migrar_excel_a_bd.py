"""
Comando para migrar archivos Excel existentes desde el sistema de archivos a la base de datos
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import os
from administracion.models import ArchivoExcel
from utils.binary_excel_fields import store_excel_file


class Command(BaseCommand):
    help = 'Migra archivos Excel existentes desde el sistema de archivos a la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué archivos se migrarían sin ejecutar cambios',
        )
        parser.add_argument(
            '--delete-originals',
            action='store_true',
            help='Elimina los archivos originales después de migrarlos exitosamente',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        delete_originals = options['delete_originals']
        
        self.stdout.write("=== MIGRACIÓN DE ARCHIVOS EXCEL A BASE DE DATOS ===\n")
        
        # Directorio de archivos Excel
        archivos_dir = Path(settings.MEDIA_ROOT) / 'archivos_turnos'
        
        if not archivos_dir.exists():
            self.stdout.write(
                self.style.WARNING(f"Directorio no encontrado: {archivos_dir}")
            )
            return
        
        # Buscar archivos Excel
        archivos_excel = list(archivos_dir.glob('*.xlsx'))
        
        if not archivos_excel:
            self.stdout.write(
                self.style.WARNING("No se encontraron archivos Excel para migrar")
            )
            return
        
        self.stdout.write(f"Archivos encontrados: {len(archivos_excel)}")
        
        migrados = 0
        errores = 0
        omitidos = 0
        
        for archivo_path in archivos_excel:
            try:
                # Verificar si ya existe en BD
                if ArchivoExcel.objects.filter(nombre_archivo=archivo_path.name).exists():
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  Ya existe en BD: {archivo_path.name}")
                    )
                    omitidos += 1
                    continue
                
                if dry_run:
                    self.stdout.write(f"[DRY-RUN] Migraría: {archivo_path.name}")
                    continue
                
                # Determinar tipo de archivo
                tipo_archivo = (ArchivoExcel.TIPO_HISTORIAL 
                              if 'historial' in archivo_path.name.lower() 
                              else ArchivoExcel.TIPO_INDIVIDUAL)
                
                # Leer archivo
                with open(archivo_path, 'rb') as f:
                    archivo_base64 = store_excel_file(f.read(), archivo_path.name)
                
                # Obtener metadatos del archivo
                stat = archivo_path.stat()
                tamaño_bytes = stat.st_size
                
                # Crear descripción basada en el nombre
                descripcion = self._generar_descripcion(archivo_path.name, tipo_archivo)
                
                # Crear registro en BD
                archivo_excel = ArchivoExcel.objects.create(
                    nombre_archivo=archivo_path.name,
                    tipo_archivo=tipo_archivo,
                    archivo_excel=archivo_base64,
                    descripcion=descripcion,
                    tamaño_bytes=tamaño_bytes,
                    # fecha_creacion se asigna automáticamente
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Migrado: {archivo_path.name} (ID: {archivo_excel.id})")
                )
                
                # Eliminar archivo original si se solicitó
                if delete_originals:
                    archivo_path.unlink()
                    self.stdout.write(f"   🗑️  Archivo original eliminado")
                
                migrados += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error migrando {archivo_path.name}: {str(e)}")
                )
                errores += 1
        
        # Resumen
        self.stdout.write("\n=== RESUMEN DE MIGRACIÓN ===")
        self.stdout.write(f"Archivos encontrados: {len(archivos_excel)}")
        self.stdout.write(f"Migrados exitosamente: {migrados}")
        self.stdout.write(f"Omitidos (ya existían): {omitidos}")
        self.stdout.write(f"Errores: {errores}")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n[DRY-RUN] No se realizaron cambios reales. Use sin --dry-run para ejecutar.")
            )
        elif migrados > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ Migración completada. {migrados} archivos ahora están en la base de datos.")
            )
            if not delete_originals:
                self.stdout.write(
                    "💡 Tip: Use --delete-originals para eliminar los archivos originales después de migrarlos."
                )
    
    def _generar_descripcion(self, nombre_archivo, tipo_archivo):
        """Genera descripción basada en el nombre del archivo"""
        if tipo_archivo == ArchivoExcel.TIPO_HISTORIAL:
            return "Historial maestro de turnos archivados (migrado desde archivo local)"
        
        # Para archivos individuales, intentar extraer información del nombre
        if '--' in nombre_archivo:
            partes = nombre_archivo.replace('.xlsx', '').split('--')
            if len(partes) >= 4:
                return f"Archivado el {partes[1]} a las {partes[2].replace('-', ':')} - {partes[3]} (migrado desde archivo local)"
        
        return "Archivo individual de turnos archivados (migrado desde archivo local)"
