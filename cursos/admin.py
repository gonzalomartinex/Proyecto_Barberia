from django.contrib import admin
from django import forms
from .models import Curso, InscripcionCurso

# Formulario temporal para deploy - reemplazar utils
class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = '__all__'

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    form = CursoForm
    list_display = ('titulo', 'dia', 'hora', 'total_inscriptos', 'estado_curso')
    list_filter = ('dia',)
    search_fields = ('titulo', 'descripcion')
    readonly_fields = ('total_inscriptos', 'estado_curso')
    
    def total_inscriptos(self, obj):
        return obj.total_inscriptos()
    total_inscriptos.short_description = 'Inscriptos'
    
    def estado_curso(self, obj):
        try:
            if obj.pk and obj.curso_pasado():  # Solo verificar si el objeto ya está guardado
                return "✅ Finalizado"
            else:
                return "🟡 Activo"
        except (AttributeError, TypeError, ValueError):
            return "⚪ Pendiente"
    estado_curso.short_description = 'Estado'

@admin.register(InscripcionCurso)
class InscripcionCursoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'curso', 'fecha_inscripcion')
    list_filter = ('fecha_inscripcion', 'curso')
    search_fields = ('usuario__nombre', 'usuario__apellido', 'usuario__email', 'curso__titulo')
    readonly_fields = ('fecha_inscripcion',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario', 'curso')
