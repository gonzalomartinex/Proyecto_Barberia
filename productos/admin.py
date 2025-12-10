from django.contrib import admin
from .models import Producto
from utils.forms import ProductoForm

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    form = ProductoForm
    list_display = ('nombre', 'precio', 'orden')
    list_filter = ('precio',)
    search_fields = ('nombre',)
    list_editable = ('precio', 'orden')
    ordering = ('orden', 'nombre')
