from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json
from rest_framework import generics, permissions
from .models import Servicio
from .serializers import ServicioSerializer
from .forms import ServicioForm

# Create your views here.

class ServicioListCreateView(generics.ListCreateAPIView):
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer
    permission_classes = [permissions.IsAuthenticated]

class ServicioRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer
    permission_classes = [permissions.IsAuthenticated]

def ServicioListView(request):
    servicios = Servicio.objects.all()
    return render(request, 'servicios.html', {'servicios': servicios})

def admin_required(view_func):
    decorated_view_func = login_required(user_passes_test(lambda u: u.is_staff)(view_func))
    return decorated_view_func

@method_decorator(admin_required, name='dispatch')
class ServicioCreateView(CreateView):
    model = Servicio
    form_class = ServicioForm
    template_name = 'servicio_form.html'
    success_url = reverse_lazy('servicio-lista')

@method_decorator(admin_required, name='dispatch')
class ServicioUpdateView(UpdateView):
    model = Servicio
    form_class = ServicioForm
    template_name = 'servicio_form.html'
    success_url = reverse_lazy('servicio-lista')

@method_decorator(admin_required, name='dispatch')
class ServicioDeleteView(DeleteView):
    model = Servicio
    template_name = 'servicio_confirm_delete.html'
    success_url = reverse_lazy('servicio-lista')
    
    def delete(self, request, *args, **kwargs):
        """
        Elimina el servicio y proporciona mensaje informativo sobre Cloudinary
        """
        servicio = self.get_object()
        servicio_nombre = servicio.nombre
        tiene_imagen = bool(servicio.imagen)
        imagen_url = str(servicio.imagen.url) if tiene_imagen else None
        
        # La eliminación automática la maneja la señal pre_delete
        response = super().delete(request, *args, **kwargs)
        
        # Mensaje informativo
        if tiene_imagen:
            messages.success(
                request, 
                f'Servicio "{servicio_nombre}" eliminado correctamente. '
                f'Su imagen también fue eliminada automáticamente de Cloudinary.'
            )
        else:
            messages.success(
                request, 
                f'Servicio "{servicio_nombre}" eliminado correctamente.'
            )
        
        return response

@csrf_exempt
@login_required
def reordenar_servicios(request):
    """Vista AJAX para reordenar servicios"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permisos insuficientes'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            orden_ids = data.get('orden', [])
            
            # Actualizar el orden de cada servicio
            for index, servicio_id in enumerate(orden_ids):
                Servicio.objects.filter(id=servicio_id).update(orden=index)
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})
