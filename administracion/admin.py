from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import path
from django.contrib import messages
from django.utils.html import format_html
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie, csrf_exempt
from django.utils.decorators import method_decorator
from .models import RegistroServicios, ArchivoExcel, BackupBaseDatos
import base64
import os

@admin.register(RegistroServicios)
class RegistroServiciosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'cliente', 'barbero', 'servicio')
    list_filter = ('fecha', 'barbero', 'servicio')
    search_fields = ('cliente__nombre', 'barbero__nombre', 'servicio__nombre')
    readonly_fields = ('fecha',)
    date_hierarchy = 'fecha'



@admin.register(BackupBaseDatos)
class BackupBaseDatosAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_creacion', 'tipo_backup', 'get_tamaño_mb', 'get_estado_display', 'get_acciones')
    list_filter = ('tipo_backup', 'fecha_creacion')
    readonly_fields = ('fecha_creacion', 'tamaño_bytes')
    search_fields = ('descripcion',)
    
    def has_add_permission(self, request):
        return False  # No permitir crear backups desde el admin normal
    
    def has_change_permission(self, request, obj=None):
        return False  # Solo lectura desde el listado
    
    def get_tamaño_mb(self, obj):
        return f"{obj.get_tamaño_mb()} MB"
    get_tamaño_mb.short_description = "Tamaño (MB)"
    
    def get_estado_display(self, obj):
        return format_html(
            '<span style="color: green; font-weight: bold;">✓ Completado</span>'
        )
    get_estado_display.short_description = "Estado"
    
    def get_acciones(self, obj):
        return format_html(
            '<a class="button" href="descargar/{}/">Descargar</a>',
            obj.pk
        )
    get_acciones.short_description = "Acciones"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('crear-backup/', self.admin_site.admin_view(self.crear_backup_view), name='crear_backup'),
            path('descargar/<int:backup_id>/', self.admin_site.admin_view(self.descargar_backup), name='descargar_backup'),
            path('restaurar/', self.restaurar_backup_view_secure, name='restaurar_backup'),
        ]
        return custom_urls + urls
    
    @csrf_exempt
    def restaurar_backup_view_secure(self, request):
        """Vista segura para restauración sin CSRF (solo para admin autenticado)"""
        # Verificar que el usuario esté autenticado y sea admin
        if not request.user.is_authenticated:
            return HttpResponseRedirect('/admin/login/?next=' + request.path)
        
        if not request.user.is_staff or not request.user.is_superuser:
            messages.error(request, 'No tienes permisos para realizar esta acción')
            return HttpResponseRedirect('/admin/')
        
        # Forzar procesamiento de archivos si es POST
        if request.method == 'POST':
            # Asegurar que Django procese los archivos correctamente
            request._dont_enforce_csrf_checks = True
        
        # Llamar a la vista original
        return self.restaurar_backup_view(request)
    
    def get_tamaño_mb(self, obj):
        return f"{obj.get_tamaño_mb()} MB"
    get_tamaño_mb.short_description = "Tamaño"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Gestión de Backups de Base de Datos'
        
        # Agregar botones personalizados
        extra_context['custom_buttons'] = [
            {
                'url': 'crear-backup/',
                'name': 'Crear Backup',
                'class': 'addlink'
            },
            {
                'url': 'restaurar/',
                'name': 'Restaurar Backup', 
                'class': 'changelink'
            }
        ]
        
        return super().changelist_view(request, extra_context=extra_context)

    def crear_backup_view(self, request):
        """Vista para crear un backup desde el admin"""
        if request.method == 'POST':
            tipo_backup = request.POST.get('tipo_backup', 'full')
            incluir_media = request.POST.get('incluir_media') == 'on'
            nombre_backup = request.POST.get('nombre', '')
            descripcion = request.POST.get('descripcion', '')
            
            try:
                # Ejecutar comando de backup
                from django.core.management import call_command
                import tempfile
                import os
                from pathlib import Path
                
                # Crear archivo temporal
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                    temp_path = temp_file.name
                
                # Crear directorio temporal específico para el backup
                import tempfile
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Ejecutar comando de backup en directorio temporal
                    if tipo_backup == 'full':
                        call_command('crear_backup', 
                                   output_dir=temp_dir,
                                   format='full',
                                   include_media=incluir_media)
                    else:
                        call_command('crear_backup',
                                   output_dir=temp_dir, 
                                   format=tipo_backup,
                                   include_media=incluir_media)
                    
                    # Encontrar el archivo creado en el directorio temporal
                    backup_dir = Path(temp_dir)
                    backup_files = list(backup_dir.glob('backup_*'))
                    
                    if backup_files:
                        backup_file = backup_files[0]  # Solo debería haber uno
                        
                        # Leer archivo y convertir a base64
                        with open(backup_file, 'rb') as f:
                            file_content = f.read()
                        
                        backup_base64 = base64.b64encode(file_content).decode('utf-8')
                        
                        # Usar el nombre proporcionado por el usuario o uno por defecto
                        backup_name = nombre_backup.strip() if nombre_backup.strip() else f'Backup {tipo_backup} {timezone.now().strftime("%d/%m/%Y %H:%M")}'
                        
                        backup_obj = BackupBaseDatos.objects.create(
                            nombre=backup_name,
                            tipo_backup=tipo_backup,
                            archivo_backup=f"data:application/zip;base64,{backup_base64}",
                            descripcion=descripcion or f'Backup {tipo_backup} creado desde admin',
                            tamaño_bytes=len(file_content),
                            incluye_media=incluir_media
                        )
                        
                        messages.success(request, f'Backup "{backup_name}" creado exitosamente (ID: {backup_obj.id})')
                    else:
                        messages.error(request, 'No se pudo encontrar el archivo de backup creado')
                
                return HttpResponseRedirect('../')
                
            except Exception as e:
                messages.error(request, f'Error creando backup: {str(e)}')
                
        context = {
            'title': 'Crear Nuevo Backup',
            'opts': self.model._meta,
        }
        return render(request, 'admin/administracion/crear_backup.html', context)

    def descargar_backup(self, request, backup_id):
        """Vista para descargar un backup"""
        try:
            backup = BackupBaseDatos.objects.get(id=backup_id)
            
            # Obtener el contenido del archivo decodificado
            file_bytes = backup.get_archivo_backup_bytes()
            if not file_bytes:
                messages.error(request, 'El backup no contiene datos válidos')
                return HttpResponseRedirect('../')
            
            # Crear respuesta con el archivo real
            response = HttpResponse(file_bytes, content_type='application/zip')
            filename = backup.get_nombre_archivo()
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except BackupBaseDatos.DoesNotExist:
            messages.error(request, 'Backup no encontrado')
            return HttpResponseRedirect('../')
        except Exception as e:
            messages.error(request, f'Error descargando backup: {str(e)}')
            return HttpResponseRedirect('../')
    
    def restaurar_backup_view(self, request):
        """Vista para restaurar un backup - VERSIÓN ROBUSTA"""
        if request.method == 'POST':
            backup_file = request.FILES.get('backup_file')
            restaurar_media = request.POST.get('restaurar_media') == 'on'
            
            if not backup_file:
                messages.error(request, 'Debe seleccionar un archivo de backup')
            else:
                try:
                    # Guardar archivo temporalmente y restaurar
                    import tempfile
                    import os
                    from django.core.management import call_command
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(backup_file.name)[1]) as temp_file:
                        for chunk in backup_file.chunks():
                            temp_file.write(chunk)
                        temp_file_path = temp_file.name
                    
                    # Ejecutar comando de restauración
                    call_command('restaurar_backup', temp_file_path, force=True, restore_media=restaurar_media)
                    
                    messages.success(request, f'Backup {backup_file.name} restaurado exitosamente.')
                    
                    # Limpiar archivo temporal
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                    
                    return HttpResponseRedirect('../')
                    
                except Exception as e:
                    messages.error(request, f'Error procesando backup: {str(e)}')
        
        context = {
            'title': 'Restaurar Backup',
            'opts': self.model._meta,
            'has_view_permission': True,
            'has_change_permission': True,
            'app_label': self.model._meta.app_label,
            'model_name': self.model._meta.model_name,
        }
        return render(request, 'admin/administracion/restaurar_backup.html', context)


@admin.register(ArchivoExcel)
class ArchivoExcelAdmin(admin.ModelAdmin):
    list_display = ('nombre_archivo', 'tipo_archivo', 'cantidad_turnos', 'get_tamaño_mb', 'fecha_creacion')
    list_filter = ('tipo_archivo', 'fecha_creacion', 'fecha_periodo_inicio')
    search_fields = ('nombre_archivo', 'descripcion')
    readonly_fields = ('fecha_creacion', 'tamaño_bytes', 'get_tamaño_mb')
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Información del Archivo', {
            'fields': ('nombre_archivo', 'tipo_archivo', 'descripcion', 'version')
        }),
        ('Contenido', {
            'fields': ('archivo_excel',),
            'description': 'El archivo Excel se almacena como base64 en la base de datos'
        }),
        ('Período Archivado', {
            'fields': ('fecha_periodo_inicio', 'fecha_periodo_fin', 'cantidad_turnos')
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'tamaño_bytes', 'archivo_padre'),
            'classes': ('collapse',)
        }),
    )
    
    def get_tamaño_mb(self, obj):
        return f"{obj.get_tamaño_mb()} MB"
    get_tamaño_mb.short_description = "Tamaño (MB)"
    
    def has_add_permission(self, request):
        return False  # Los archivos Excel se crean automáticamente
    
    def has_change_permission(self, request, obj=None):
        return False  # Solo lectura
