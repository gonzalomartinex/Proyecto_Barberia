from django.contrib import admin
from .models import Curso, InscripcionCurso

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'dia', 'hora', 'total_inscriptos')
    list_filter = ('dia',)
    search_fields = ('titulo', 'descripcion')
    readonly_fields = ('total_inscriptos',)
    
    def total_inscriptos(self, obj):
        return obj.total_inscriptos()
    total_inscriptos.short_description = 'Inscriptos'

@admin.register(InscripcionCurso)
class InscripcionCursoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'curso', 'fecha_inscripcion')
    list_filter = ('fecha_inscripcion', 'curso')
    search_fields = ('usuario__nombre', 'usuario__apellido', 'usuario__email', 'curso__titulo')
    readonly_fields = ('fecha_inscripcion',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario', 'curso')
