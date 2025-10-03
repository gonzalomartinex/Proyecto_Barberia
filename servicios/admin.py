from django.contrib import admin
from .models import Servicio

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio')
    list_filter = ('precio',)
    search_fields = ('nombre', 'descripcion')
    list_editable = ('precio',)
