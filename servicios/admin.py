from django.contrib import admin
from .models import Servicio
from utils.forms import ServicioForm

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    form = ServicioForm
    list_display = ('nombre', 'precio', 'orden')
    list_filter = ('precio',)
    search_fields = ('nombre', 'descripcion')
    list_editable = ('precio', 'orden')
    ordering = ('orden', 'nombre')
