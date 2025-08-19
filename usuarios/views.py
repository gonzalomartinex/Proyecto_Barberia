from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from .models import Usuario, Barbero, TrabajoBarbero, RedSocial
from .serializers import UsuarioSerializer
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.shortcuts import redirect
from .models import Usuario
from django.db import models

from django import forms
from django.http import HttpResponseForbidden
from .forms import BarberoForm, get_redsocial_formset
from django.forms import inlineformset_factory, modelform_factory
# Create your views here.

class PerfilUsuarioView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def cambiar_estado_usuario(request, pk):
    try:
        usuario = Usuario.objects.get(pk=pk)
    except Usuario.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    estado = request.data.get('estado')
    if estado is not None:
        usuario.estado = estado
        if estado:
            usuario.contador_faltas = 0
        usuario.save()
        return Response({'success': True, 'estado': usuario.estado})
    return Response({'error': 'Debe enviar el campo estado (true/false)'}, status=status.HTTP_400_BAD_REQUEST)

def barberos_list(request):
    barberos = Barbero.objects.all()
    return render(request, 'barberos.html', {'barberos': barberos})

def barbero_perfil(request, pk):
    barbero = get_object_or_404(Barbero, pk=pk)
    return render(request, 'barbero_perfil.html', {'barbero': barbero})

@login_required
def perfil_usuario(request):
    return render(request, 'perfil.html', {'user': request.user})

class RegistroForm(forms.ModelForm):
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repetir contraseña', widget=forms.PasswordInput)
    fecha_nacimiento = forms.DateField(label='Fecha de nacimiento', widget=forms.DateInput(attrs={'type': 'date'}))
    codigo_pais = forms.CharField(label='Código de país', initial='+54', max_length=5)
    telefono_numero = forms.CharField(label='Teléfono', max_length=20)
    class Meta:
        model = Usuario
        fields = ['email', 'nombre', 'apellido', 'fecha_nacimiento']
    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Las contraseñas no coinciden')
        return cleaned_data

def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.set_password(form.cleaned_data['password1'])
            usuario.estado = False  # Usuario deshabilitado por defecto
            # Unir código de país y número
            usuario.telefono = f"{form.cleaned_data['codigo_pais']}{form.cleaned_data['telefono_numero']}"
            usuario.save()
            messages.success(request, 'Usuario registrado correctamente. Debe ser habilitado por la barbería antes de poder reservar turnos.')
            return redirect('login')
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})

class TrabajoBarberoForm(forms.ModelForm):
    class Meta:
        model = TrabajoBarbero
        fields = ['imagen']

@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
def cargar_trabajo_barbero(request, barbero_id):
    barbero = get_object_or_404(Barbero, pk=barbero_id)
    if request.method == 'POST':
        form = TrabajoBarberoForm(request.POST, request.FILES)
        if form.is_valid():
            trabajo = form.save(commit=False)
            trabajo.barbero = barbero
            trabajo.save()
            messages.success(request, 'Imagen de trabajo cargada correctamente.')
            return redirect('barbero-perfil', pk=barbero.id)
    else:
        form = TrabajoBarberoForm()
    return render(request, 'cargar_trabajo_barbero.html', {'form': form, 'barbero': barbero})

@login_required
def eliminar_trabajo_barbero(request, trabajo_id):
    trabajo = get_object_or_404(TrabajoBarbero, pk=trabajo_id)
    if not request.user.is_staff:
        return HttpResponseForbidden()
    barbero_id = trabajo.barbero.id
    trabajo.delete()
    messages.success(request, 'Imagen eliminada correctamente.')
    return redirect('barbero-perfil', pk=barbero_id)

@login_required
def registrar_barbero(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = BarberoForm(request.POST, request.FILES)
        if form.is_valid():
            barbero = form.save()
            messages.success(request, 'Barbero registrado correctamente.')
            return redirect('barberos-list')
    else:
        form = BarberoForm()
    return render(request, 'registrar_barbero.html', {'form': form})

@login_required
def editar_barbero(request, pk):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    barbero = get_object_or_404(Barbero, pk=pk)
    if request.method == 'POST':
        form = BarberoForm(request.POST, request.FILES, instance=barbero)
        if form.is_valid():
            barbero = form.save()
            messages.success(request, 'Barbero editado correctamente.')
            return redirect('barbero-perfil', pk=barbero.id)
    else:
        form = BarberoForm(instance=barbero)
    return render(request, 'editar_barbero.html', {'form': form, 'barbero': barbero})

@login_required
def eliminar_barbero(request, pk):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    barbero = get_object_or_404(Barbero, pk=pk)
    if request.method == 'POST':
        barbero.delete()
        messages.success(request, 'Barbero eliminado correctamente.')
        return redirect('barberos-list')
    return render(request, 'eliminar_barbero.html', {'barbero': barbero})

@login_required
def gestionar_redes_barbero(request, barbero_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    barbero = get_object_or_404(Barbero, pk=barbero_id)
    RedSocialForm = modelform_factory(RedSocial, fields=("url", "nombre"))
    if request.method == 'POST':
        # Guardar nuevo orden
        if 'nuevo_orden' in request.POST and request.POST['nuevo_orden']:
            ids = request.POST['nuevo_orden'].split(',')
            for idx, rid in enumerate(ids):
                try:
                    red = RedSocial.objects.get(pk=rid, barbero=barbero)
                    red.orden = idx
                    red.save()
                except RedSocial.DoesNotExist:
                    continue
            messages.success(request, 'Orden de redes sociales actualizado.')
            return redirect('gestionar-redes-barbero', barbero_id=barbero.id)
        # Eliminar red social
        if 'eliminar_red' in request.POST:
            red_id = request.POST.get('eliminar_red')
            red = get_object_or_404(RedSocial, pk=red_id, barbero=barbero)
            red.delete()
            messages.success(request, 'Red social eliminada.')
            return redirect('gestionar-redes-barbero', barbero_id=barbero.id)
        # Agregar red social
        form = RedSocialForm(request.POST)
        if form.is_valid():
            nueva_red = form.save(commit=False)
            nueva_red.barbero = barbero
            # Poner al final
            max_orden = barbero.redes_sociales.aggregate(maxo=models.Max('orden'))['maxo'] or 0
            nueva_red.orden = max_orden + 1
            nueva_red.save()
            messages.success(request, 'Red social agregada.')
            return redirect('gestionar-redes-barbero', barbero_id=barbero.id)
    else:
        form = RedSocialForm()
    redes = barbero.redes_sociales.order_by('orden', 'id')
    return render(request, 'gestionar_redes_barbero.html', {'barbero': barbero, 'form': form, 'redes': redes})

@login_required
def editar_perfil_usuario(request):
    user = request.user
    if request.method == 'POST':
        user.nombre = request.POST.get('nombre', user.nombre)
        user.apellido = request.POST.get('apellido', user.apellido)
        user.email = request.POST.get('email', user.email)
        user.telefono = request.POST.get('telefono', user.telefono)
        # La fecha de nacimiento solo se puede cambiar desde el admin site
        user.save()
        messages.success(request, 'Datos actualizados correctamente.')
        return redirect('perfil_usuario')
    return render(request, 'editar_perfil.html', {'user': user})
