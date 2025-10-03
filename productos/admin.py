from django.contrib import admin
from .models import Producto

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio')
    list_filter = ('precio',)
    search_fields = ('nombre',)
    list_editable = ('precio',)
