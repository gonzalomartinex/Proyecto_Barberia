from django.contrib import admin
from .models import Turno

class TurnoAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'barbero', 'cliente', 'servicio', 'estado')
    list_filter = ('barbero', 'estado', 'servicio')
    search_fields = ('barbero__nombre', 'cliente__nombre', 'cliente__apellido', 'servicio__nombre')
    ordering = ('-fecha_hora',)

admin.site.register(Turno, TurnoAdmin)
