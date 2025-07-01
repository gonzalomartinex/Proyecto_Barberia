from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
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
