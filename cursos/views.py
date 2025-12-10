from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Curso, InscripcionCurso
from .forms import CursoForm

def cursos_list(request):
    cursos = Curso.objects.all().order_by('-dia', '-hora')
    
    # Añadir información sobre si cada curso ya pasó
    for curso in cursos:
        curso.ya_paso = curso.curso_pasado()
    
    return render(request, 'cursos.html', {'cursos': cursos})

def detalle_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    
    # Verificar si el usuario está inscripto
    esta_inscripto = False
    if request.user.is_authenticated:
        esta_inscripto = InscripcionCurso.objects.filter(
            usuario=request.user, 
            curso=curso
        ).exists()
    
    # Verificar si el curso ya pasó
    curso_ya_paso = curso.curso_pasado()
    
    # Para admins: obtener lista de emails de inscriptos
    emails_inscriptos = []
    if request.user.is_authenticated and request.user.is_superuser:
        emails_inscriptos = list(curso.inscriptos.values_list('email', flat=True))
    
    context = {
        'curso': curso,
        'esta_inscripto': esta_inscripto,
        'curso_ya_paso': curso_ya_paso,
        'emails_inscriptos': emails_inscriptos,
        'total_inscriptos': curso.total_inscriptos()
    }
    
    return render(request, 'detalle_curso.html', context)

@user_passes_test(lambda u: u.is_superuser)
def crear_curso(request):
    if request.method == 'POST':
        form = CursoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso creado correctamente.')
            return redirect('cursos-list')
    else:
        form = CursoForm()
    return render(request, 'curso_form.html', {'form': form, 'titulo': 'Crear Curso'})

@user_passes_test(lambda u: u.is_superuser)
def editar_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    if request.method == 'POST':
        form = CursoForm(request.POST, request.FILES, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso editado correctamente.')
            return redirect('cursos-list')
    else:
        form = CursoForm(instance=curso)
    return render(request, 'curso_form.html', {'form': form, 'titulo': 'Editar Curso', 'curso': curso})

@user_passes_test(lambda u: u.is_superuser)
def eliminar_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    if request.method == 'POST':
        curso.delete()
        messages.success(request, 'Curso eliminado correctamente.')
        return redirect('cursos-list')
    return render(request, 'curso_confirm_delete.html', {'curso': curso})

@login_required
def inscribirse_curso(request, pk):
    """Vista para inscribirse a un curso"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    curso = get_object_or_404(Curso, pk=pk)
    
    try:
        # Verificar si el curso ya pasó
        if curso.curso_pasado():
            return JsonResponse({
                'error': 'No puedes inscribirte a un curso que ya ha pasado'
            }, status=400)
        
        # Verificar si ya está inscripto
        if InscripcionCurso.objects.filter(usuario=request.user, curso=curso).exists():
            return JsonResponse({
                'error': 'Ya estás inscripto en este curso'
            }, status=400)
        
        # Crear inscripción
        InscripcionCurso.objects.create(usuario=request.user, curso=curso)
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Te has inscripto correctamente al curso "{curso.titulo}"',
            'total_inscriptos': curso.total_inscriptos()
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error al inscribirse: {str(e)}'
        }, status=500)

@login_required
def desinscribirse_curso(request, pk):
    """Vista para desinscribirse de un curso"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    curso = get_object_or_404(Curso, pk=pk)
    
    try:
        # Buscar y eliminar inscripción
        inscripcion = InscripcionCurso.objects.filter(
            usuario=request.user, 
            curso=curso
        ).first()
        
        if not inscripcion:
            return JsonResponse({
                'error': 'No estás inscripto en este curso'
            }, status=400)
        
        inscripcion.delete()
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Te has desinscripto del curso "{curso.titulo}"',
            'total_inscriptos': curso.total_inscriptos()
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error al desinscribirse: {str(e)}'
        }, status=500)
