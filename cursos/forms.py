from django import forms
from .models import Curso

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['titulo', 'dia', 'hora', 'descripcion', 'imagen']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'dia': forms.Select(choices=[
                ('Lunes', 'Lunes'),
                ('Martes', 'Martes'),
                ('Miércoles', 'Miércoles'),
                ('Jueves', 'Jueves'),
                ('Viernes', 'Viernes'),
                ('Sábado', 'Sábado'),
                ('Domingo', 'Domingo'),
            ], attrs={'class': 'form-control'}),
            'hora': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
        }
