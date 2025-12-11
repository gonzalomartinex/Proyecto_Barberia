from django.db import models
from django.utils import timezone
from usuarios.models import Usuario, Barbero
from servicios.models import Servicio
from pathlib import Path
import base64

# Campos temporales para deploy - reemplazar utils
class BinaryExcelField(models.FileField):
    pass

BinaryFileField = BinaryExcelField

class RegistroServicios(models.Model):
    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='registros_servicios')
    barbero = models.ForeignKey(Barbero, on_delete=models.CASCADE, related_name='registros_servicios')
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='registros_servicios')
    fecha = models.DateTimeField()
    notas = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.fecha} - {self.cliente} - {self.servicio}"


class ArchivoExcel(models.Model):
    """
    Modelo para almacenar archivos Excel archivados en la base de datos
    """
    
    # Tipos de archivo
    TIPO_INDIVIDUAL = 'individual'
    TIPO_HISTORIAL = 'historial'
    
    TIPOS_ARCHIVO = [
        (TIPO_INDIVIDUAL, 'Archivo Individual'),
        (TIPO_HISTORIAL, 'Historial Maestro'),
    ]
    
    # Información del archivo
    nombre_archivo = models.CharField(max_length=255, help_text="Nombre original del archivo")
    tipo_archivo = models.CharField(max_length=20, choices=TIPOS_ARCHIVO, default=TIPO_INDIVIDUAL)
    descripcion = models.TextField(blank=True, help_text="Descripción del contenido del archivo")
    
    # Archivo Excel almacenado como base64
    archivo_excel = models.TextField(help_text="Archivo Excel almacenado en base64")
    
    # Metadatos
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_periodo_inicio = models.DateField(null=True, blank=True, help_text="Fecha de inicio del período archivado")
    fecha_periodo_fin = models.DateField(null=True, blank=True, help_text="Fecha de fin del período archivado")
    
    # Estadísticas del archivo
    cantidad_turnos = models.PositiveIntegerField(default=0, help_text="Cantidad de turnos archivados en este archivo")
    tamaño_bytes = models.PositiveIntegerField(default=0, help_text="Tamaño del archivo en bytes")
    
    # Control de versiones
    version = models.CharField(max_length=20, default="1.0", help_text="Versión del archivo")
    archivo_padre = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                    help_text="Archivo del cual deriva este (para historial)")
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Archivo Excel"
        verbose_name_plural = "Archivos Excel"
        indexes = [
            models.Index(fields=['fecha_creacion']),
            models.Index(fields=['tipo_archivo']),
            models.Index(fields=['fecha_periodo_inicio', 'fecha_periodo_fin']),
        ]
    
    def __str__(self):
        return f"{self.nombre_archivo} ({self.get_tipo_archivo_display()}) - {self.fecha_creacion.strftime('%Y-%m-%d %H:%M')}"
    
    def get_tamaño_mb(self):
        """Retorna el tamaño en MB"""
        if self.tamaño_bytes:
            return round(self.tamaño_bytes / (1024 * 1024), 2)
        return 0
    
    def get_descripcion_completa(self):
        """Genera una descripción completa basada en los datos"""
        if self.tipo_archivo == self.TIPO_HISTORIAL:
            return f"Historial maestro con {self.cantidad_turnos} turnos archivados"
        else:
            periodo = ""
            if self.fecha_periodo_inicio and self.fecha_periodo_fin:
                periodo = f" del {self.fecha_periodo_inicio} al {self.fecha_periodo_fin}"
            return f"Archivo individual con {self.cantidad_turnos} turnos{periodo}"
    
    def save(self, *args, **kwargs):
        """Override save para calcular metadatos automáticamente"""
        if self.archivo_excel and not self.tamaño_bytes:
            # Calcular tamaño desde base64
            try:
                excel_bytes = self.get_archivo_excel_bytes()
                if excel_bytes:
                    self.tamaño_bytes = len(excel_bytes)
            except Exception:
                pass
        
        # Generar descripción si está vacía
        if not self.descripcion:
            self.descripcion = self.get_descripcion_completa()
        
        super().save(*args, **kwargs)
    
    @classmethod
    def crear_desde_archivo_local(cls, ruta_archivo, tipo_archivo=TIPO_INDIVIDUAL, **kwargs):
        """
        Crear una instancia desde un archivo local existente
        """
        import os
        from pathlib import Path
        # Función temporal para deploy
        def store_excel_file(data, filename):
            return filename
        
        ruta = Path(ruta_archivo)
        
        if not ruta.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {ruta_archivo}")
        
        # Leer archivo
        with open(ruta, 'rb') as f:
            archivo_base64 = store_excel_file(f.read(), ruta.name)
        
        # Crear instancia
        archivo_excel = cls(
            nombre_archivo=ruta.name,
            tipo_archivo=tipo_archivo,
            archivo_excel=archivo_base64,
            tamaño_bytes=ruta.stat().st_size,
            **kwargs
        )
        
        archivo_excel.save()
        return archivo_excel
    
    def descargar_como_response(self):
        """
        Retorna una respuesta HTTP para descargar este archivo
        """
        from django.http import HttpResponse
        
        if not self.archivo_excel:
            raise ValueError("No hay archivo para descargar")
        
        try:
            # Obtener bytes usando el método helper
            file_bytes = self.get_archivo_excel_bytes()
            if not file_bytes:
                raise ValueError("No se pudieron obtener los datos del archivo")
            
            # Crear respuesta HTTP
            response = HttpResponse(
                file_bytes, 
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{self.nombre_archivo}"'
            
            return response
            
        except Exception as e:
            raise ValueError(f"Error creando respuesta de descarga: {str(e)}")

    def has_archivo_excel(self):
        """
        Verifica si el archivo Excel está presente y no está vacío
        """
        return bool(self.archivo_excel)

    def get_archivo_excel_bytes(self):
        """
        Retorna los bytes del archivo Excel decodificando desde base64
        """
        if not self.archivo_excel:
            return None
        
        try:
            # Si es un string, tratar como base64
            archivo_data = str(self.archivo_excel).strip()
            
            # Remover prefijo data: si existe
            if archivo_data.startswith('data:'):
                archivo_data = archivo_data.split(',', 1)[1]
            
            # Decodificar base64
            return base64.b64decode(archivo_data)
            
        except Exception:
            return None

class BackupBaseDatos(models.Model):
    """
    Modelo para gestionar backups de la base de datos desde el admin
    """
    
    # Tipos de backup
    TIPO_JSON = 'json'
    TIPO_SQLITE = 'sqlite'
    TIPO_COMPLETO = 'full'  # Cambiado de 'completo' a 'full' para coincidir con el comando
    
    TIPOS_BACKUP = [
        (TIPO_JSON, 'JSON (Fixtures)'),
        (TIPO_SQLITE, 'SQLite (Base de datos)'),
        (TIPO_COMPLETO, 'Completo (ZIP)'),
    ]
    
    # Información del backup
    nombre = models.CharField(max_length=255, help_text="Nombre descriptivo del backup")
    tipo_backup = models.CharField(max_length=20, choices=TIPOS_BACKUP, default=TIPO_COMPLETO)
    descripcion = models.TextField(blank=True, help_text="Descripción del backup")
    
    # Archivo de backup almacenado como base64
    archivo_backup = models.TextField(blank=True, null=True, help_text="Archivo de backup almacenado en base64")
    
    # Metadatos
    fecha_creacion = models.DateTimeField(default=timezone.now)
    tamaño_bytes = models.PositiveIntegerField(default=0, help_text="Tamaño del archivo en bytes")
    
    # Información adicional
    incluye_media = models.BooleanField(default=False, help_text="Si incluye archivos media")
    version_django = models.CharField(max_length=50, blank=True, help_text="Versión de Django")
    notas = models.TextField(blank=True, help_text="Notas adicionales sobre el backup")
    
    # Control
    creado_automaticamente = models.BooleanField(default=False, help_text="Si fue creado automáticamente")
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Backup de Base de Datos"
        verbose_name_plural = "Backups de Base de Datos"
        indexes = [
            models.Index(fields=['fecha_creacion']),
            models.Index(fields=['tipo_backup']),
        ]
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_backup_display()}) - {self.fecha_creacion.strftime('%Y-%m-%d %H:%M')}"
    
    def get_tamaño_mb(self):
        """Retorna el tamaño en MB"""
        if self.tamaño_bytes:
            return round(self.tamaño_bytes / (1024 * 1024), 2)
        return 0
    
    def get_extension_archivo(self):
        """Retorna la extensión correcta según el tipo"""
        if self.tipo_backup == self.TIPO_JSON:
            return '.json'
        elif self.tipo_backup == self.TIPO_SQLITE:
            return '.db'
        else:
            return '.zip'
    
    def get_nombre_archivo(self):
        """Genera nombre de archivo para descarga"""
        timestamp = self.fecha_creacion.strftime('%Y%m%d_%H%M%S')
        extension = self.get_extension_archivo()
        nombre_limpio = "".join(c for c in self.nombre if c.isalnum() or c in (' ', '-', '_')).rstrip()
        return f"{nombre_limpio}_{timestamp}{extension}"

    def get_archivo_backup_bytes(self):
        """
        Retorna los bytes del archivo de backup decodificando desde base64
        """
        if not self.archivo_backup:
            return None
        
        try:
            backup_data = str(self.archivo_backup).strip()
            
            # Remover prefijo data: si existe
            if backup_data.startswith('data:'):
                backup_data = backup_data.split(',', 1)[1]
            
            # Decodificar base64
            return base64.b64decode(backup_data)
            
        except Exception:
            return None
    
    def save(self, *args, **kwargs):
        """Override save para calcular metadatos automáticamente"""
        if self.archivo_backup and not self.tamaño_bytes:
            # Calcular tamaño desde base64
            try:
                backup_bytes = self.get_archivo_backup_bytes()
                if backup_bytes:
                    self.tamaño_bytes = len(backup_bytes)
            except Exception:
                pass
        
        super().save(*args, **kwargs)
    
    def descargar_como_response(self):
        """
        Retorna una respuesta HTTP para descargar este backup
        """
        from django.http import HttpResponse
        import base64
        
        if not self.archivo_backup:
            raise ValueError("No hay archivo de backup para descargar")
        
        try:
            # Obtener bytes usando el método helper
            file_bytes = self.get_archivo_backup_bytes()
            if not file_bytes:
                raise ValueError("No se pudieron obtener los datos del archivo")
            
            # Determinar content type
            if self.tipo_backup == self.TIPO_JSON:
                content_type = 'application/json'
            elif self.tipo_backup == self.TIPO_SQLITE:
                content_type = 'application/x-sqlite3'
            else:
                content_type = 'application/zip'
            
            # Crear respuesta HTTP
            response = HttpResponse(file_bytes, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{self.get_nombre_archivo()}"'
            
            return response
            
        except Exception as e:
            raise ValueError(f"Error creando respuesta de descarga: {str(e)}")
    
    @classmethod
    def crear_backup_automatico(cls, tipo_backup=TIPO_COMPLETO, incluir_media=False):
        """
        Crear un backup automáticamente usando el comando de gestión
        """
        from django.core.management import call_command
        from django.conf import settings
        from django.utils import timezone
        from pathlib import Path
        import tempfile
        import os
        import base64
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Crear backup usando el comando
            args = [
                f'--output-dir={temp_dir}', 
                f'--format={tipo_backup}'
            ]
            if incluir_media:
                args.append('--include-media')
            
            call_command('crear_backup', *args)
            
            # Buscar el archivo creado
            temp_path = Path(temp_dir)
            backup_files = list(temp_path.glob('backup_*'))
            
            if not backup_files:
                raise FileNotFoundError("No se pudo crear el archivo de backup")
            
            backup_file = backup_files[0]
            
            # Leer archivo y convertir a base64
            with open(backup_file, 'rb') as f:
                file_content = f.read()
            
            backup_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # Crear registro en BD
            backup = cls.objects.create(
                nombre=f"Backup automático {timezone.now().strftime('%d/%m/%Y %H:%M')}",
                tipo_backup=tipo_backup,
                archivo_backup=f"data:application/octet-stream;base64,{backup_base64}",
                tamaño_bytes=len(file_content),
                incluye_media=incluir_media,
                creado_automaticamente=True,
                descripcion=f"Backup automático creado desde el admin el {timezone.now().strftime('%d/%m/%Y a las %H:%M')}"
            )
            
            return backup
