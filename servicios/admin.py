from django.contrib import admin
from django import forms
from .models import Servicio

# Formulario temporal para deploy - reemplazar utils
class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = '__all__'

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    form = ServicioForm
    list_display = ('nombre', 'precio', 'orden')
    list_filter = ('precio',)
    search_fields = ('nombre', 'descripcion')
    list_editable = ('precio', 'orden')
    ordering = ('orden', 'nombre')
