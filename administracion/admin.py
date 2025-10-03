from django.contrib import admin
from .models import RegistroServicios

@admin.register(RegistroServicios)
class RegistroServiciosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'cliente', 'barbero', 'servicio')
    list_filter = ('fecha', 'barbero', 'servicio')
    search_fields = ('cliente__nombre', 'barbero__nombre', 'servicio__nombre')
    readonly_fields = ('fecha',)
    date_hierarchy = 'fecha'
