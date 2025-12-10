"""
Comando para restaurar backup de la base de datos
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.db import transaction
import os
import sqlite3
import json
import zipfile
import shutil
from pathlib import Path
import tempfile


class Command(BaseCommand):
    help = 'Restaura un backup de la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Ruta al archivo de backup a restaurar',
        )
        parser.add_argument(
            '--restore-media',
            action='store_true',
            help='Restaurar archivos media incluidos en el backup',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar restauración sin confirmación',
        )

    def handle(self, *args, **options):
        backup_file = Path(options['backup_file'])
        
        if not backup_file.exists():
            self.stdout.write(
                self.style.ERROR(f'❌ Archivo de backup no encontrado: {backup_file}')
            )
            return
        
        self.stdout.write("=== RESTAURANDO BACKUP DE LA BASE DE DATOS ===\n")
        self.stdout.write(f'📁 Archivo: {backup_file}')
        
        # Advertencia de seguridad
        if not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  ADVERTENCIA: Esta operación eliminará todos los datos actuales '
                    'y los reemplazará con los del backup.\n'
                    'Asegúrate de haber creado un backup de la base de datos actual.\n'
                )
            )
            
            confirm = input('¿Continuar con la restauración? (escriba "si" para confirmar): ')
            if confirm.lower() != 'si':
                self.stdout.write('❌ Restauración cancelada')
                return
        
        try:
            # Determinar tipo de backup
            if backup_file.suffix == '.zip':
                self._restore_full_backup(backup_file, options['restore_media'])
            elif backup_file.suffix == '.json':
                self._restore_json_backup(backup_file)
            elif backup_file.suffix == '.db':
                self._restore_sqlite_backup(backup_file)
            else:
                raise ValueError(f"Formato de backup no soportado: {backup_file.suffix}")
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Backup restaurado exitosamente desde: {backup_file}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error restaurando backup: {str(e)}')
            )
            raise

    def _restore_json_backup(self, backup_file):
        """Restaurar desde backup JSON (fixtures)"""
        self.stdout.write('📦 Restaurando desde backup JSON...')
        
        # Limpiar base de datos
        self.stdout.write('🗑️  Limpiando base de datos actual...')
        call_command('flush', '--noinput')
        
        # Cargar datos
        self.stdout.write('📥 Cargando datos...')
        call_command('loaddata', str(backup_file))
        
        self.stdout.write('✅ Backup JSON restaurado')

    def _restore_sqlite_backup(self, backup_file):
        """Restaurar desde backup SQLite"""
        self.stdout.write('📦 Restaurando desde backup SQLite...')
        
        # Ruta de la base de datos actual
        db_path = settings.DATABASES['default']['NAME']
        
        # Crear backup de la BD actual antes de reemplazar
        current_backup = f"{db_path}.backup_{self._get_timestamp()}"
        if os.path.exists(db_path):
            self.stdout.write(f'💾 Creando backup de BD actual: {current_backup}')
            shutil.copy2(db_path, current_backup)
        
        # Reemplazar base de datos
        self.stdout.write('🔄 Reemplazando base de datos...')
        shutil.copy2(str(backup_file), db_path)
        
        self.stdout.write('✅ Backup SQLite restaurado')

    def _restore_full_backup(self, backup_file, restore_media=False):
        """Restaurar desde backup completo (ZIP)"""
        self.stdout.write('📦 Restaurando desde backup completo...')
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extraer archivo ZIP
            self.stdout.write('📂 Extrayendo backup...')
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(temp_path)
            
            # Verificar contenido del backup
            metadata_file = temp_path / 'backup_info.json'
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                self.stdout.write(f'📋 Información del backup:')
                self.stdout.write(f'   - Fecha: {metadata.get("created_at", "N/A")}')
                self.stdout.write(f'   - Tipo: {metadata.get("backup_type", "N/A")}')
                self.stdout.write(f'   - Django: {metadata.get("django_version", "N/A")}')
            
            # 1. Restaurar base de datos SQLite si existe
            sqlite_file = temp_path / 'database.db'
            if sqlite_file.exists():
                self.stdout.write('🔄 Restaurando base de datos SQLite...')
                db_path = settings.DATABASES['default']['NAME']
                
                # Backup de la BD actual
                if os.path.exists(db_path):
                    current_backup = f"{db_path}.backup_{self._get_timestamp()}"
                    self.stdout.write(f'💾 Backup de BD actual: {current_backup}')
                    shutil.copy2(db_path, current_backup)
                
                shutil.copy2(str(sqlite_file), db_path)
            
            # 2. Restaurar datos JSON si existe y no hay SQLite
            json_file = temp_path / 'data.json'
            if json_file.exists() and not sqlite_file.exists():
                self.stdout.write('📥 Restaurando datos desde JSON...')
                call_command('flush', '--noinput')
                call_command('loaddata', str(json_file))
            
            # 3. Restaurar archivos media si se solicita
            if restore_media:
                media_dir = temp_path / 'media'
                if media_dir.exists():
                    self.stdout.write('📁 Restaurando archivos media...')
                    media_root = Path(settings.MEDIA_ROOT)
                    
                    # Crear backup de media actual
                    if media_root.exists():
                        media_backup = media_root.parent / f'media_backup_{self._get_timestamp()}'
                        self.stdout.write(f'💾 Backup de media actual: {media_backup}')
                        shutil.copytree(media_root, media_backup, ignore_errors=True)
                    
                    # Copiar archivos media del backup
                    for item in media_dir.rglob('*'):
                        if item.is_file():
                            relative_path = item.relative_to(media_dir)
                            target_path = media_root / relative_path
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(item, target_path)
        
            # 4. Recrear tabla de backups (que se excluye de los backups optimizados)
            self._recrear_tabla_backups()
        
        self.stdout.write('✅ Backup completo restaurado')

    def _recrear_tabla_backups(self):
        """Recrea la tabla de backups después de una restauración"""
        self.stdout.write('🔧 Recreando tabla de administración de backups...')
        
        try:
            db_path = settings.DATABASES['default']['NAME']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar si ya existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='administracion_backupbasedatos'")
            exists = cursor.fetchall()
            
            if not exists:
                # Crear la tabla
                create_table_sql = '''
                CREATE TABLE administracion_backupbasedatos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre VARCHAR(255) NOT NULL,
                    tipo_backup VARCHAR(20) NOT NULL DEFAULT 'full',
                    descripcion TEXT NOT NULL DEFAULT '',
                    archivo_backup TEXT,
                    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    tamaño_bytes INTEGER NOT NULL DEFAULT 0,
                    incluye_media BOOLEAN NOT NULL DEFAULT 0,
                    version_django VARCHAR(50) NOT NULL DEFAULT '',
                    notas TEXT NOT NULL DEFAULT '',
                    creado_automaticamente BOOLEAN NOT NULL DEFAULT 0
                );
                '''
                
                cursor.execute(create_table_sql)
                conn.commit()
                self.stdout.write('✅ Tabla de backups recreada correctamente')
            else:
                self.stdout.write('✅ Tabla de backups ya existe')
                
            conn.close()
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Advertencia al recrear tabla de backups: {e}')
            )

    def _get_timestamp(self):
        """Obtener timestamp para nombres de archivo"""
        from django.utils import timezone
        return timezone.now().strftime('%Y%m%d_%H%M%S')
