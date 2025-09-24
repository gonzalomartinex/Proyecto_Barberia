from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .models import Curso
from .forms import CursoForm

def cursos_list(request):
    cursos = Curso.objects.all()
    return render(request, 'cursos.html', {'cursos': cursos})

def detalle_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    return render(request, 'detalle_curso.html', {'curso': curso})

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
