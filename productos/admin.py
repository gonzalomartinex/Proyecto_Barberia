from django.contrib import admin
from django import forms
from .models import Producto

# Formulario temporal para deploy - reemplazar utils
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    form = ProductoForm
    list_display = ('nombre', 'precio', 'orden')
    list_filter = ('precio',)
    search_fields = ('nombre',)
    list_editable = ('precio', 'orden')
    ordering = ('orden', 'nombre')
