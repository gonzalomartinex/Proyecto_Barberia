from django import forms
from .models import Curso

class DateWidget(forms.DateInput):
    """Widget personalizado para fechas que maneja mejor los valores iniciales"""
    
    def __init__(self, attrs=None):
        default_attrs = {'type': 'date', 'class': 'form-control'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)
    
    def format_value(self, value):
        """Asegura que el valor se formatee correctamente para el input HTML5"""
        if value is None:
            return ''
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return str(value)

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['titulo', 'dia', 'hora', 'descripcion', 'imagen']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Curso de Barbería Clásica'}),
            'dia': DateWidget(),  # Usar el widget personalizado
            'hora': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Describe el contenido, objetivos y requisitos del curso...'
            }),
            'imagen': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['titulo'].label = 'Título del curso'
        self.fields['dia'].label = 'Fecha del curso'
        self.fields['hora'].label = 'Hora de inicio'
        self.fields['descripcion'].label = 'Descripción'
        self.fields['imagen'].label = 'Imagen del curso'
        self.fields['imagen'].help_text = 'Opcional. Formatos: JPG, PNG, WEBP'
        self.fields['imagen'].help_text = 'Opcional. Formatos: JPG, PNG, WEBP'
