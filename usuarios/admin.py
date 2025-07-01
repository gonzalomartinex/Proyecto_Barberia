from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario, Barbero, TrabajoBarbero, RedSocial

class UsuarioAdmin(BaseUserAdmin):
    list_display = ('email', 'nombre', 'apellido', 'telefono', 'estado', 'contador_faltas', 'es_administrador', 'is_staff')
    list_filter = ('estado', 'es_administrador', 'is_staff')
    search_fields = ('email', 'nombre', 'apellido', 'telefono')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('nombre', 'apellido', 'telefono', 'fecha_nacimiento', 'foto_perfil')}),
        ('Permisos', {'fields': ('estado', 'contador_faltas', 'es_administrador', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('fecha_registro', 'last_login')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'apellido', 'telefono', 'fecha_nacimiento', 'password1', 'password2', 'estado', 'es_administrador', 'is_staff'),
        }),
    )
    readonly_fields = ('fecha_registro', 'last_login')

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Barbero)
admin.site.register(TrabajoBarbero)
admin.site.register(RedSocial)
