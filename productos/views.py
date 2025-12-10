from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework import generics, permissions
from django import forms
from .models import Producto
from .serializers import ProductoSerializer

# Formulario temporal para deploy - reemplazar utils
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'

# Create your views here.

class ProductoListCreateView(generics.ListCreateAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticated]

class ProductoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticated]

def admin_required(view_func):
    decorated_view_func = login_required(user_passes_test(lambda u: u.is_staff)(view_func))
    return decorated_view_func

@method_decorator(admin_required, name='dispatch')
class ProductoCreateView(CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_form.html'
    success_url = reverse_lazy('producto-lista')

@method_decorator([admin_required, csrf_exempt], name='dispatch')
class ProductoUpdateView(UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_form.html'
    success_url = reverse_lazy('producto-lista')
    
    def post(self, request, *args, **kwargs):
        """Handle both CSRF-protected and CSRF-exempt requests"""
        # Si la petición viene con un token CSRF válido, procesarla normalmente
        # Si no, permitirla igualmente (para uso como API)
        return super().post(request, *args, **kwargs)

@method_decorator(admin_required, name='dispatch')
class ProductoDeleteView(DeleteView):
    model = Producto
    template_name = 'producto_confirm_delete.html'
    success_url = reverse_lazy('producto-lista')

def ProductoListView(request):
    productos = Producto.objects.all()
    return render(request, 'productos.html', {'productos': productos})

@csrf_exempt
@login_required
def reordenar_productos(request):
    """Vista AJAX para reordenar productos"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permisos insuficientes'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            orden_ids = data.get('orden', [])
            
            # Actualizar el orden de cada producto
            for index, producto_id in enumerate(orden_ids):
                Producto.objects.filter(id=producto_id).update(orden=index)
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})
