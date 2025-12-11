"""
Comando mejorado para crear backup con soporte para Cloudinary
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
import cloudinary.api
import requests
from urllib.parse import urlparse


class Command(BaseCommand):
    help = 'Crea un backup completo compatible con Cloudinary'

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
            '--include-cloudinary',
            action='store_true',
            help='Descargar y incluir imágenes de Cloudinary en el backup',
        )
        parser.add_argument(
            '--cloudinary-backup-mode',
            type=str,
            choices=['urls', 'download', 'both'],
            default='urls',
            help='Modo de backup de Cloudinary: urls (solo URLs), download (descargar imágenes), both (ambos)',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== CREANDO BACKUP COMPATIBLE CON CLOUDINARY ===\n")
        
        # Determinar directorio de salida
        if options['output_dir']:
            backup_dir = Path(options['output_dir'])
        else:
            backup_dir = Path(settings.MEDIA_ROOT) / 'backups'
        
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Nombre del archivo con timestamp
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            if options['format'] == 'json':
                backup_file = self._create_json_backup(backup_dir, timestamp, options)
            elif options['format'] == 'sqlite':
                backup_file = self._create_sqlite_backup(backup_dir, timestamp, options)
            else:  # full
                backup_file = self._create_full_backup(backup_dir, timestamp, options)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Backup creado exitosamente: {backup_file}'))
            
            # Información adicional sobre Cloudinary
            if options['include_cloudinary']:
                self._show_cloudinary_info()
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creando backup: {e}'))

    def _create_json_backup(self, backup_dir, timestamp, options):
        """Crear backup JSON con información de Cloudinary"""
        backup_file = backup_dir / f'backup_cloudinary_{timestamp}.json'
        
        self.stdout.write('📄 Creando backup JSON...')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            # Crear fixtures
            call_command('dumpdata', 
                        '--natural-foreign', 
                        '--natural-primary',
                        '--indent=2',
                        '--output', temp_file.name,
                        '--exclude', 'contenttypes',
                        '--exclude', 'auth.permission',
                        '--exclude', 'administracion.backupbasedatos')
            
            # Leer y procesar el JSON
            with open(temp_file.name, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Agregar información de Cloudinary si se solicita
            if options['include_cloudinary']:
                data = self._process_cloudinary_data(data, options['cloudinary_backup_mode'])
        
        # Guardar archivo final
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        os.unlink(temp_file.name)
        self.stdout.write('✅ Backup JSON creado')
        return backup_file

    def _create_sqlite_backup(self, backup_dir, timestamp, options):
        """Crear backup SQLite con metadatos de Cloudinary"""
        backup_file = backup_dir / f'backup_cloudinary_{timestamp}.db'
        
        self.stdout.write('🗄️ Creando backup SQLite...')
        
        # Obtener ruta de la base de datos
        db_path = settings.DATABASES['default']['NAME']
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
        
        # Crear copia sin la tabla de backups
        source = sqlite3.connect(db_path)
        target = sqlite3.connect(str(backup_file))
        
        # Copiar todas las tablas excepto la de backups
        cursor = source.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table_name in tables:
            table = table_name[0]
            if table not in ['administracion_backupbasedatos', 'sqlite_sequence']:
                # Copiar estructura
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{table}'")
                create_sql = cursor.fetchone()
                if create_sql:
                    target.execute(create_sql[0])
                
                # Copiar datos
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                if rows:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns_info = cursor.fetchall()
                    placeholders = ','.join(['?' for _ in columns_info])
                    target.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
        
        # Agregar tabla de metadatos de Cloudinary
        if options['include_cloudinary']:
            self._add_cloudinary_metadata_table(target)
        
        target.commit()
        source.close()
        target.close()
        
        self.stdout.write('✅ Backup SQLite creado')
        return backup_file

    def _create_full_backup(self, backup_dir, timestamp, options):
        """Crear backup completo con soporte para Cloudinary"""
        backup_file = backup_dir / f'backup_cloudinary_full_{timestamp}.zip'
        
        self.stdout.write('📦 Creando backup completo...')
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 1. Crear backup JSON
            json_file = temp_path / 'data.json'
            self.stdout.write('  - Creando datos JSON...')
            call_command('dumpdata', 
                        '--natural-foreign', 
                        '--natural-primary',
                        '--indent=2',
                        '--output', str(json_file),
                        '--exclude', 'contenttypes',
                        '--exclude', 'auth.permission',
                        '--exclude', 'administracion.backupbasedatos')
            
            # 2. Crear backup SQLite
            sqlite_file = temp_path / 'database.db'
            self.stdout.write('  - Creando base de datos SQLite...')
            self._copy_database_to_file(sqlite_file, options)
            
            # 3. Procesar imágenes de Cloudinary
            cloudinary_dir = temp_path / 'cloudinary_images'
            if options['include_cloudinary']:
                self._backup_cloudinary_images(cloudinary_dir, options['cloudinary_backup_mode'])
            
            # 4. Crear metadatos
            metadata_file = temp_path / 'backup_info.json'
            self._create_metadata_file(metadata_file, options)
            
            # 5. Crear ZIP
            self.stdout.write('  - Comprimiendo archivos...')
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(json_file, 'data.json')
                zipf.write(sqlite_file, 'database.db')
                zipf.write(metadata_file, 'backup_info.json')
                
                # Incluir imágenes de Cloudinary si se descargaron
                if options['include_cloudinary'] and cloudinary_dir.exists():
                    for file_path in cloudinary_dir.rglob('*'):
                        if file_path.is_file():
                            relative_path = file_path.relative_to(cloudinary_dir)
                            zipf.write(file_path, f'cloudinary_images/{relative_path}')
        
        self.stdout.write('✅ Backup completo creado')
        return backup_file

    def _process_cloudinary_data(self, data, backup_mode):
        """Procesar datos con información de Cloudinary"""
        cloudinary_urls = []
        
        for item in data:
            model = item.get('model', '')
            fields = item.get('fields', {})
            
            # Buscar campos de imagen en modelos relevantes
            image_fields = []
            if model == 'productos.producto':
                image_fields = ['imagen']
            elif model == 'cursos.curso':
                image_fields = ['imagen']
            elif model == 'usuarios.usuario':
                image_fields = ['foto_perfil']
            
            for field in image_fields:
                if field in fields and fields[field]:
                    url = fields[field]
                    if 'cloudinary' in url:
                        cloudinary_urls.append({
                            'model': model,
                            'pk': item.get('pk'),
                            'field': field,
                            'url': url,
                            'public_id': self._extract_public_id(url)
                        })
        
        # Agregar información de Cloudinary al backup
        if cloudinary_urls:
            data.append({
                'model': 'backup.cloudinary_metadata',
                'fields': {
                    'created_at': timezone.now().isoformat(),
                    'total_images': len(cloudinary_urls),
                    'images': cloudinary_urls,
                    'backup_mode': backup_mode
                }
            })
        
        return data

    def _backup_cloudinary_images(self, output_dir, backup_mode):
        """Descargar imágenes de Cloudinary si se solicita"""
        if backup_mode in ['download', 'both']:
            self.stdout.write('  - Descargando imágenes de Cloudinary...')
            output_dir.mkdir(exist_ok=True)
            
            # Obtener URLs de imágenes de la base de datos
            from productos.models import Producto
            from cursos.models import Curso
            from django.contrib.auth import get_user_model
            
            Usuario = get_user_model()
            downloaded = 0
            
            # Descargar imágenes de productos
            for producto in Producto.objects.exclude(imagen__exact=''):
                if self._download_cloudinary_image(producto.imagen, output_dir / f'producto_{producto.pk}.jpg'):
                    downloaded += 1
            
            # Descargar imágenes de cursos
            for curso in Curso.objects.exclude(imagen__exact=''):
                if self._download_cloudinary_image(curso.imagen, output_dir / f'curso_{curso.pk}.jpg'):
                    downloaded += 1
            
            # Descargar fotos de perfil
            for usuario in Usuario.objects.exclude(foto_perfil__exact=''):
                if self._download_cloudinary_image(usuario.foto_perfil, output_dir / f'usuario_{usuario.pk}.jpg'):
                    downloaded += 1
            
            self.stdout.write(f'    ✅ {downloaded} imágenes descargadas')

    def _download_cloudinary_image(self, url, output_path):
        """Descargar una imagen de Cloudinary"""
        try:
            if not url or not url.startswith('http'):
                return False
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            self.stdout.write(f'    ⚠️ Error descargando {url}: {e}')
            return False

    def _extract_public_id(self, cloudinary_url):
        """Extraer public_id de una URL de Cloudinary"""
        try:
            parsed = urlparse(cloudinary_url)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                # Formato típico: /cloud_name/image/upload/v1234567890/public_id.ext
                return '/'.join(path_parts[3:]).split('.')[0]  # Eliminar extensión
        except:
            pass
        return None

    def _add_cloudinary_metadata_table(self, connection):
        """Agregar tabla con metadatos de Cloudinary"""
        cursor = connection.cursor()
        
        # Crear tabla de metadatos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cloudinary_backup_metadata (
                id INTEGER PRIMARY KEY,
                created_at TEXT,
                cloud_name TEXT,
                total_images INTEGER,
                metadata_json TEXT
            )
        ''')
        
        # Recopilar metadatos
        try:
            cloud_name = settings.CLOUDINARY_STORAGE['CLOUD_NAME']
        except:
            cloud_name = 'unknown'
        
        metadata = self._collect_cloudinary_metadata()
        
        cursor.execute('''
            INSERT INTO cloudinary_backup_metadata 
            (created_at, cloud_name, total_images, metadata_json)
            VALUES (?, ?, ?, ?)
        ''', (
            timezone.now().isoformat(),
            cloud_name,
            len(metadata),
            json.dumps(metadata, ensure_ascii=False)
        ))

    def _collect_cloudinary_metadata(self):
        """Recopilar metadatos de imágenes de Cloudinary"""
        metadata = []
        
        try:
            from productos.models import Producto
            from cursos.models import Curso
            from django.contrib.auth import get_user_model
            
            Usuario = get_user_model()
            
            # Productos
            for producto in Producto.objects.exclude(imagen__exact=''):
                if 'cloudinary' in producto.imagen:
                    metadata.append({
                        'model': 'productos.producto',
                        'pk': producto.pk,
                        'field': 'imagen',
                        'url': producto.imagen,
                        'public_id': self._extract_public_id(producto.imagen)
                    })
            
            # Cursos
            for curso in Curso.objects.exclude(imagen__exact=''):
                if 'cloudinary' in curso.imagen:
                    metadata.append({
                        'model': 'cursos.curso',
                        'pk': curso.pk,
                        'field': 'imagen',
                        'url': curso.imagen,
                        'public_id': self._extract_public_id(curso.imagen)
                    })
            
            # Usuarios
            for usuario in Usuario.objects.exclude(foto_perfil__exact=''):
                if 'cloudinary' in usuario.foto_perfil:
                    metadata.append({
                        'model': 'usuarios.usuario',
                        'pk': usuario.pk,
                        'field': 'foto_perfil',
                        'url': usuario.foto_perfil,
                        'public_id': self._extract_public_id(usuario.foto_perfil)
                    })
                    
        except Exception as e:
            self.stdout.write(f'⚠️ Error recopilando metadatos: {e}')
        
        return metadata

    def _copy_database_to_file(self, output_file, options):
        """Copiar base de datos a archivo"""
        db_path = settings.DATABASES['default']['NAME']
        source = sqlite3.connect(db_path)
        target = sqlite3.connect(str(output_file))
        
        cursor = source.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table_name in tables:
            table = table_name[0]
            if table not in ['administracion_backupbasedatos', 'sqlite_sequence']:
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{table}'")
                create_sql = cursor.fetchone()
                if create_sql:
                    target.execute(create_sql[0])
                
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                if rows:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns_info = cursor.fetchall()
                    placeholders = ','.join(['?' for _ in columns_info])
                    target.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
        
        if options['include_cloudinary']:
            self._add_cloudinary_metadata_table(target)
        
        target.commit()
        source.close()
        target.close()

    def _create_metadata_file(self, output_file, options):
        """Crear archivo de metadatos"""
        metadata = {
            'created_at': timezone.now().isoformat(),
            'django_version': self._get_django_version(),
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'apps': list(settings.INSTALLED_APPS),
            'includes_cloudinary': options['include_cloudinary'],
            'cloudinary_backup_mode': options.get('cloudinary_backup_mode', 'urls'),
            'backup_type': 'cloudinary_compatible',
            'cloudinary_config': self._get_cloudinary_config()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def _get_django_version(self):
        """Obtener versión de Django"""
        import django
        return django.get_version()

    def _get_cloudinary_config(self):
        """Obtener configuración de Cloudinary (sin credenciales)"""
        try:
            return {
                'cloud_name': settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', 'unknown'),
                'configured': True
            }
        except:
            return {'configured': False}

    def _show_cloudinary_info(self):
        """Mostrar información sobre Cloudinary"""
        try:
            result = cloudinary.api.usage()
            self.stdout.write('\n📊 Información de Cloudinary:')
            self.stdout.write(f'  - Imágenes: {result.get("resources", 0)}')
            self.stdout.write(f'  - Almacenamiento: {result.get("bytes", 0) / 1024 / 1024:.2f} MB')
            self.stdout.write(f'  - Límite mensual: {result.get("limit", "N/A")}')
        except Exception as e:
            self.stdout.write(f'⚠️ No se pudo obtener información de Cloudinary: {e}')
