from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from .models import Usuario, Barbero, TrabajoBarbero, RedSocial

# Formularios temporales para deploy - reemplazar utils
class BarberoForm(forms.ModelForm):
    class Meta:
        model = Barbero
        fields = '__all__'

class UsuarioAdminForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = '__all__'

class UsuarioAdmin(BaseUserAdmin):
    form = UsuarioAdminForm
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

@admin.register(Barbero)
class BarberoAdmin(admin.ModelAdmin):
    form = BarberoForm
    list_display = ('nombre', 'telefono', 'fecha_nacimiento', 'orden')
    search_fields = ('nombre', 'telefono', 'dni')
    list_filter = ('fecha_nacimiento',)
    list_editable = ('orden',)
    ordering = ('orden', 'nombre')

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(TrabajoBarbero)
admin.site.register(RedSocial)
