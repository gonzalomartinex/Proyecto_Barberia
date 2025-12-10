"""
Comando para crear backup completo de la base de datos
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.utils import timezone
import os
import sqlite3
import json
import zipfile
from pathlib import Path
import tempfile


class Command(BaseCommand):
    help = 'Crea un backup completo de la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Directorio donde guardar el backup (por defecto: media/backups)',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'sqlite', 'full'],
            default='full',
            help='Formato del backup: json (fixtures), sqlite (copia BD), full (ambos en ZIP)',
        )
        parser.add_argument(
            '--include-media',
            action='store_true',
            help='Incluir archivos media en el backup',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== CREANDO BACKUP DE LA BASE DE DATOS ===\n")
        
        # Determinar directorio de salida
        if options['output_dir']:
            backup_dir = Path(options['output_dir'])
        else:
            backup_dir = Path(settings.MEDIA_ROOT) / 'backups'
        
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Nombre del archivo con timestamp
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        format_type = options['format']
        
        try:
            if format_type == 'json':
                backup_file = self._create_json_backup(backup_dir, timestamp)
            elif format_type == 'sqlite':
                backup_file = self._create_sqlite_backup(backup_dir, timestamp)
            else:  # full
                backup_file = self._create_full_backup(backup_dir, timestamp, options['include_media'])
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Backup creado exitosamente: {backup_file}')
            )
            
            # Mostrar información del archivo
            file_size = backup_file.stat().st_size
            size_mb = round(file_size / (1024 * 1024), 2)
            
            self.stdout.write(f'📁 Ubicación: {backup_file}')
            self.stdout.write(f'📏 Tamaño: {size_mb} MB')
            self.stdout.write(f'🕒 Fecha: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creando backup: {str(e)}')
            )
            raise

    def _create_json_backup(self, backup_dir, timestamp):
        """Crear backup en formato JSON (fixtures)"""
        backup_file = backup_dir / f'backup_json_{timestamp}.json'
        
        self.stdout.write('📦 Creando backup JSON (fixtures)...')
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            call_command('dumpdata', 
                        '--natural-foreign', 
                        '--natural-primary',
                        '--indent', '2',
                        '--exclude', 'administracion.BackupBaseDatos',
                        stdout=f)
        
        self.stdout.write('✅ Backup JSON creado')
        return backup_file

    def _create_sqlite_backup(self, backup_dir, timestamp):
        """Crear backup de la base de datos SQLite"""
        backup_file = backup_dir / f'backup_sqlite_{timestamp}.db'
        
        self.stdout.write('📦 Creando backup SQLite (sin tabla de backups)...')
        
        # Obtener ruta de la base de datos
        db_path = settings.DATABASES['default']['NAME']
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
        
        # Crear copia sin la tabla de backups
        source = sqlite3.connect(db_path)
        target = sqlite3.connect(str(backup_file))
        
        # Obtener todas las tablas excepto la de backups
        cursor = source.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table_name in tables:
            table = table_name[0]
            # Excluir tabla de backups y tablas del sistema
            if table not in ['administracion_backupbasedatos', 'sqlite_sequence']:
                # Copiar estructura de tabla
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{table}'")
                create_sql = cursor.fetchone()
                if create_sql:
                    target.execute(create_sql[0])
                
                # Copiar datos
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                if rows:
                    # Obtener info de columnas
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns_info = cursor.fetchall()
                    placeholders = ','.join(['?' for _ in columns_info])
                    target.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
        
        target.commit()
        source.close()
        target.close()
        
        self.stdout.write('✅ Backup SQLite creado')
        return backup_file

    def _create_full_backup(self, backup_dir, timestamp, include_media=False):
        """Crear backup completo (JSON + SQLite + opcionalmente media)"""
        backup_file = backup_dir / f'backup_full_{timestamp}.zip'
        
        self.stdout.write('📦 Creando backup completo...')
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 1. Crear backup JSON (EXCLUYENDO backups existentes)
            self.stdout.write('  - Exportando datos (JSON)...')
            json_file = temp_path / 'data.json'
            with open(json_file, 'w', encoding='utf-8') as f:
                call_command('dumpdata', 
                            '--natural-foreign', 
                            '--natural-primary',
                            '--indent', '2',
                            '--exclude', 'administracion.BackupBaseDatos',
                            stdout=f)
            
            # 2. Copiar base de datos SQLite (EXCLUYENDO tabla de backups)
            self.stdout.write('  - Copiando base de datos SQLite (sin tabla de backups)...')
            db_path = settings.DATABASES['default']['NAME']
            sqlite_file = temp_path / 'database.db'
            
            # Crear copia sin la tabla de backups
            source = sqlite3.connect(db_path)
            target = sqlite3.connect(str(sqlite_file))
            
            # Obtener todas las tablas excepto la de backups
            cursor = source.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table_name in tables:
                table = table_name[0]
                # Excluir tabla de backups y tablas del sistema
                if table not in ['administracion_backupbasedatos', 'sqlite_sequence']:
                    # Copiar estructura de tabla
                    cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{table}'")
                    create_sql = cursor.fetchone()
                    if create_sql:
                        target.execute(create_sql[0])
                    
                    # Copiar datos
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    if rows:
                        # Obtener info de columnas
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns_info = cursor.fetchall()
                        placeholders = ','.join(['?' for _ in columns_info])
                        target.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
            
            target.commit()
            source.close()
            target.close()
            
            # 3. Crear archivo de metadatos
            self.stdout.write('  - Creando metadatos...')
            metadata = {
                'created_at': timezone.now().isoformat(),
                'django_version': self._get_django_version(),
                'database_engine': settings.DATABASES['default']['ENGINE'],
                'apps': self._get_installed_apps(),
                'includes_media': include_media,
                'backup_type': 'full'
            }
            
            metadata_file = temp_path / 'backup_info.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 4. Crear archivo ZIP
            self.stdout.write('  - Comprimiendo archivos...')
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(json_file, 'data.json')
                zipf.write(sqlite_file, 'database.db')
                zipf.write(metadata_file, 'backup_info.json')
                
                # 5. Incluir archivos media si se solicita
                if include_media:
                    self.stdout.write('  - Incluyendo archivos media...')
                    media_root = Path(settings.MEDIA_ROOT)
                    if media_root.exists():
                        for file_path in media_root.rglob('*'):
                            if file_path.is_file():
                                # Evitar incluir otros backups y archivos temporales
                                relative_parts = file_path.relative_to(media_root).parts
                                if ('backups' not in relative_parts and 
                                    not file_path.name.startswith('.') and
                                    not file_path.name.endswith('.tmp')):
                                    relative_path = file_path.relative_to(media_root)
                                    zipf.write(file_path, f'media/{relative_path}')
        
        self.stdout.write('✅ Backup completo creado')
        return backup_file

    def _get_django_version(self):
        """Obtener versión de Django"""
        import django
        return django.get_version()

    def _get_installed_apps(self):
        """Obtener lista de apps instaladas"""
        return settings.INSTALLED_APPS
