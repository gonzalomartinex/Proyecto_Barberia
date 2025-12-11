"""
Comando para migrar backups antiguos con imágenes binarias a Cloudinary
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
import os
import sqlite3
import json
import zipfile
from pathlib import Path
import tempfile
import base64
from io import BytesIO


class Command(BaseCommand):
    help = 'Migra backups antiguos con imágenes binarias a formato Cloudinary'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Ruta al archivo de backup antiguo a migrar',
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Directorio donde guardar el backup migrado',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar qué se haría sin hacer cambios reales',
        )

    def handle(self, *args, **options):
        backup_file = Path(options['backup_file'])
        dry_run = options['dry_run']
        
        if not backup_file.exists():
            self.stdout.write(
                self.style.ERROR(f'❌ Archivo de backup no encontrado: {backup_file}')
            )
            return
        
        self.stdout.write("=== MIGRANDO BACKUP BINARIO A CLOUDINARY ===\n")
        self.stdout.write(f'📁 Archivo original: {backup_file}')
        
        if dry_run:
            self.stdout.write('🔍 MODO DRY-RUN (solo análisis, no se harán cambios)')
        
        try:
            # Determinar directorio de salida
            if options['output_dir']:
                output_dir = Path(options['output_dir'])
            else:
                output_dir = backup_file.parent
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Procesar según el tipo de archivo
            if backup_file.suffix == '.zip':
                self._migrate_zip_backup(backup_file, output_dir, dry_run)
            elif backup_file.suffix == '.db':
                self._migrate_sqlite_backup(backup_file, output_dir, dry_run)
            elif backup_file.suffix == '.json':
                self._migrate_json_backup(backup_file, output_dir, dry_run)
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Formato de backup no soportado: {backup_file.suffix}')
                )
                return
                
            if not dry_run:
                self.stdout.write(self.style.SUCCESS('✅ Migración completada exitosamente'))
            else:
                self.stdout.write('🔍 Análisis completado. Usa sin --dry-run para ejecutar la migración')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error durante la migración: {e}'))

    def _migrate_zip_backup(self, backup_file, output_dir, dry_run):
        """Migrar backup ZIP completo"""
        self.stdout.write('📦 Procesando backup ZIP...')
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'backup_migrated_{timestamp}.zip'
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extraer backup original
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(temp_path)
            
            # Migrar base de datos si existe
            db_file = temp_path / 'database.db'
            if db_file.exists():
                self.stdout.write('  - Migrando base de datos SQLite...')
                migrated_db = temp_path / 'database_migrated.db'
                self._migrate_sqlite_data(db_file, migrated_db, dry_run)
                if not dry_run:
                    db_file.unlink()  # Eliminar original
                    migrated_db.rename(db_file)  # Renombrar migrado
            
            # Migrar JSON si existe
            json_file = temp_path / 'data.json'
            if json_file.exists():
                self.stdout.write('  - Migrando datos JSON...')
                migrated_json = temp_path / 'data_migrated.json'
                self._migrate_json_data(json_file, migrated_json, dry_run)
                if not dry_run:
                    json_file.unlink()
                    migrated_json.rename(json_file)
            
            # Actualizar metadatos
            metadata_file = temp_path / 'backup_info.json'
            if metadata_file.exists() and not dry_run:
                self._update_metadata(metadata_file)
            
            # Crear ZIP migrado
            if not dry_run:
                self.stdout.write('  - Creando backup migrado...')
                with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in temp_path.rglob('*'):
                        if file_path.is_file():
                            relative_path = file_path.relative_to(temp_path)
                            zipf.write(file_path, relative_path)
                
                self.stdout.write(f'✅ Backup migrado guardado en: {output_file}')

    def _migrate_sqlite_backup(self, backup_file, output_dir, dry_run):
        """Migrar backup SQLite"""
        self.stdout.write('🗄️ Procesando backup SQLite...')
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'backup_migrated_{timestamp}.db'
        
        self._migrate_sqlite_data(backup_file, output_file, dry_run)
        
        if not dry_run:
            self.stdout.write(f'✅ Backup SQLite migrado guardado en: {output_file}')

    def _migrate_json_backup(self, backup_file, output_dir, dry_run):
        """Migrar backup JSON"""
        self.stdout.write('📄 Procesando backup JSON...')
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'backup_migrated_{timestamp}.json'
        
        self._migrate_json_data(backup_file, output_file, dry_run)
        
        if not dry_run:
            self.stdout.write(f'✅ Backup JSON migrado guardado en: {output_file}')

    def _migrate_sqlite_data(self, input_file, output_file, dry_run):
        """Migrar datos binarios en SQLite a URLs de Cloudinary"""
        migrated_count = 0
        
        if dry_run:
            # Solo analizar
            conn = sqlite3.connect(str(input_file))
            cursor = conn.cursor()
            
            # Analizar productos
            cursor.execute("SELECT COUNT(*) FROM productos_producto WHERE imagen IS NOT NULL AND imagen != ''")
            productos_count = cursor.fetchone()[0]
            self.stdout.write(f'    🔍 Productos con imágenes binarias: {productos_count}')
            
            # Analizar cursos
            cursor.execute("SELECT COUNT(*) FROM cursos_curso WHERE imagen IS NOT NULL AND imagen != ''")
            cursos_count = cursor.fetchone()[0]
            self.stdout.write(f'    🔍 Cursos con imágenes binarias: {cursos_count}')
            
            # Analizar usuarios
            cursor.execute("SELECT COUNT(*) FROM usuarios_usuario WHERE foto_perfil IS NOT NULL AND foto_perfil != ''")
            usuarios_count = cursor.fetchone()[0]
            self.stdout.write(f'    🔍 Usuarios con fotos de perfil binarias: {usuarios_count}')
            
            conn.close()
            return
        
        # Migrar realmente
        shutil.copy2(input_file, output_file)
        conn = sqlite3.connect(str(output_file))
        cursor = conn.cursor()
        
        try:
            # Migrar imágenes de productos
            cursor.execute("SELECT id, imagen FROM productos_producto WHERE imagen IS NOT NULL AND imagen != ''")
            productos = cursor.fetchall()
            
            for producto_id, imagen_data in productos:
                if imagen_data and not imagen_data.startswith('http'):
                    # Es dato binario, migrar a Cloudinary
                    cloudinary_url = self._upload_binary_to_cloudinary(imagen_data, f'producto_{producto_id}')
                    if cloudinary_url:
                        cursor.execute("UPDATE productos_producto SET imagen = ? WHERE id = ?", 
                                     (cloudinary_url, producto_id))
                        migrated_count += 1
            
            # Migrar imágenes de cursos
            cursor.execute("SELECT id, imagen FROM cursos_curso WHERE imagen IS NOT NULL AND imagen != ''")
            cursos = cursor.fetchall()
            
            for curso_id, imagen_data in cursos:
                if imagen_data and not imagen_data.startswith('http'):
                    cloudinary_url = self._upload_binary_to_cloudinary(imagen_data, f'curso_{curso_id}')
                    if cloudinary_url:
                        cursor.execute("UPDATE cursos_curso SET imagen = ? WHERE id = ?", 
                                     (cloudinary_url, curso_id))
                        migrated_count += 1
            
            # Migrar fotos de perfil de usuarios
            cursor.execute("SELECT id, foto_perfil FROM usuarios_usuario WHERE foto_perfil IS NOT NULL AND foto_perfil != ''")
            usuarios = cursor.fetchall()
            
            for usuario_id, foto_data in usuarios:
                if foto_data and not foto_data.startswith('http'):
                    cloudinary_url = self._upload_binary_to_cloudinary(foto_data, f'usuario_{usuario_id}')
                    if cloudinary_url:
                        cursor.execute("UPDATE usuarios_usuario SET foto_perfil = ? WHERE id = ?", 
                                     (cloudinary_url, usuario_id))
                        migrated_count += 1
            
            conn.commit()
            self.stdout.write(f'    ✅ {migrated_count} imágenes migradas a Cloudinary')
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _migrate_json_data(self, input_file, output_file, dry_run):
        """Migrar datos JSON con imágenes binarias"""
        if dry_run:
            self.stdout.write('    🔍 Analizando datos JSON...')
            return
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        migrated_count = 0
        
        for item in data:
            model = item.get('model', '')
            fields = item.get('fields', {})
            pk = item.get('pk')
            
            # Migrar productos
            if model == 'productos.producto' and 'imagen' in fields:
                imagen_data = fields['imagen']
                if imagen_data and not imagen_data.startswith('http'):
                    cloudinary_url = self._upload_binary_to_cloudinary(imagen_data, f'producto_{pk}')
                    if cloudinary_url:
                        fields['imagen'] = cloudinary_url
                        migrated_count += 1
            
            # Migrar cursos
            elif model == 'cursos.curso' and 'imagen' in fields:
                imagen_data = fields['imagen']
                if imagen_data and not imagen_data.startswith('http'):
                    cloudinary_url = self._upload_binary_to_cloudinary(imagen_data, f'curso_{pk}')
                    if cloudinary_url:
                        fields['imagen'] = cloudinary_url
                        migrated_count += 1
            
            # Migrar usuarios
            elif model == 'usuarios.usuario' and 'foto_perfil' in fields:
                foto_data = fields['foto_perfil']
                if foto_data and not foto_data.startswith('http'):
                    cloudinary_url = self._upload_binary_to_cloudinary(foto_data, f'usuario_{pk}')
                    if cloudinary_url:
                        fields['foto_perfil'] = cloudinary_url
                        migrated_count += 1
        
        # Guardar JSON migrado
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(f'    ✅ {migrated_count} imágenes migradas en JSON')

    def _upload_binary_to_cloudinary(self, binary_data, public_id):
        """Subir datos binarios a Cloudinary y obtener URL"""
        try:
            import cloudinary.uploader
            
            # Decodificar datos binarios (asumiendo base64)
            if isinstance(binary_data, str):
                try:
                    image_data = base64.b64decode(binary_data)
                except:
                    # Si no es base64, tratar como datos raw
                    image_data = binary_data.encode() if isinstance(binary_data, str) else binary_data
            else:
                image_data = binary_data
            
            # Subir a Cloudinary
            result = cloudinary.uploader.upload(
                BytesIO(image_data),
                public_id=public_id,
                overwrite=True,
                resource_type="image"
            )
            
            return result.get('secure_url')
            
        except Exception as e:
            self.stdout.write(f'    ⚠️ Error subiendo imagen {public_id}: {e}')
            return None

    def _update_metadata(self, metadata_file):
        """Actualizar metadatos del backup migrado"""
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        metadata['migrated_at'] = timezone.now().isoformat()
        metadata['migration_type'] = 'binary_to_cloudinary'
        metadata['backup_type'] = metadata.get('backup_type', 'unknown') + '_migrated'
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
