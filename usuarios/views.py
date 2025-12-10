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
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from django import forms
from django.http import HttpResponseForbidden
from .forms import BarberoForm, get_redsocial_formset, UsuarioForm, CambiarContrasenaForm
from django.forms import inlineformset_factory, modelform_factory

# Función auxiliar para formatear nombres
def formatear_nombre(nombre):
    """
    Formatea un nombre para que cada palabra tenga la primera letra en mayúscula
    y el resto en minúscula. Maneja múltiples espacios y palabras.
    
    Ejemplos:
    - "juan carlos" → "Juan Carlos"
    - "MARÍA JOSÉ" → "María José" 
    - "  ana  maria  " → "Ana Maria"
    """
    if not nombre:
        return nombre
    
    # Dividir por espacios, filtrar palabras vacías y formatear cada palabra
    palabras = [palabra.strip().capitalize() for palabra in nombre.split() if palabra.strip()]
    
    # Unir con un solo espacio
    return ' '.join(palabras)

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

@csrf_exempt
@login_required
def reordenar_barberos(request):
    """Vista AJAX para reordenar barberos"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permisos insuficientes'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            orden_ids = data.get('orden', [])
            
            # Actualizar el orden de cada barbero
            for index, barbero_id in enumerate(orden_ids):
                Barbero.objects.filter(id=barbero_id).update(orden=index)
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

def barbero_perfil(request, pk):
    barbero = get_object_or_404(Barbero, pk=pk)
    return render(request, 'barbero_perfil.html', {'barbero': barbero})

@login_required
def perfil_usuario(request):
    from turnos.models import Turno
    from django.utils import timezone
    from django.db.models import Count
    
    # Obtener turnos activos del usuario (ocupados, no expirados)
    now = timezone.now()
    turnos_activos = Turno.objects.filter(
        cliente=request.user,
        estado='ocupado',
        fecha_hora__gte=now
    ).select_related('barbero', 'servicio').order_by('fecha_hora')
    
    # Obtener estadísticas del usuario
    total_turnos = Turno.objects.filter(cliente=request.user).count()
    turnos_completados = Turno.objects.filter(cliente=request.user, estado='completado').count()
    turnos_cancelados = Turno.objects.filter(cliente=request.user, estado='cancelado').count()
    
    # Barbero favorito (con más turnos)
    barbero_favorito = Turno.objects.filter(
        cliente=request.user,
        estado__in=['ocupado', 'completado']
    ).values('barbero__nombre').annotate(
        total=Count('barbero')
    ).order_by('-total').first()
    
    estadisticas = {
        'total_turnos': total_turnos,
        'turnos_completados': turnos_completados,
        'turnos_cancelados': turnos_cancelados,
        'turnos_activos_count': turnos_activos.count(),
        'barbero_favorito': barbero_favorito['barbero__nombre'] if barbero_favorito else 'Ninguno'
    }
    
    return render(request, 'perfil.html', {
        'user': request.user,
        'turnos_activos': turnos_activos,
        'estadisticas': estadisticas
    })

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
    
    def clean_nombre(self):
        """Aplica formateo automático al nombre"""
        nombre = self.cleaned_data.get('nombre')
        return formatear_nombre(nombre)
    
    def clean_apellido(self):
        """Aplica formateo automático al apellido"""
        apellido = self.cleaned_data.get('apellido')
        return formatear_nombre(apellido)

def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.set_password(form.cleaned_data['password1'])
            usuario.estado = False  # Usuario deshabilitado por defecto
            
            # Formatear nombre y apellido con mayúsculas iniciales
            usuario.nombre = formatear_nombre(usuario.nombre)
            usuario.apellido = formatear_nombre(usuario.apellido)
            
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
        form = UsuarioForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil_usuario')
    else:
        form = UsuarioForm(instance=user)
    return render(request, 'editar_perfil.html', {'form': form, 'user': user})

@user_passes_test(lambda u: u.is_superuser)
def gestionar_usuarios(request):
    """Vista para gestionar todos los usuarios del sistema"""
    usuarios = Usuario.objects.all()
    
    # Filtros
    nombre_filtro = request.GET.get('nombre', '')
    email_filtro = request.GET.get('email', '')
    telefono_filtro = request.GET.get('telefono', '')
    estado_filtro = request.GET.get('estado', '')
    faltas_filtro = request.GET.get('faltas', '')
    
    # Aplicar filtros
    if nombre_filtro:
        # Mejorar búsqueda de nombre/apellido para permitir "nombre apellido"
        palabras = nombre_filtro.strip().split()
        
        if len(palabras) == 1:
            # Búsqueda con una sola palabra (como antes)
            usuarios = usuarios.filter(
                models.Q(nombre__icontains=palabras[0]) | 
                models.Q(apellido__icontains=palabras[0])
            )
        elif len(palabras) == 2:
            # Búsqueda con dos palabras: "nombre apellido" o "apellido nombre"
            palabra1, palabra2 = palabras[0], palabras[1]
            usuarios = usuarios.filter(
                # Caso: "nombre apellido" - ambas palabras deben coincidir
                (models.Q(nombre__icontains=palabra1) & models.Q(apellido__icontains=palabra2)) |
                # Caso: "apellido nombre" - ambas palabras deben coincidir
                (models.Q(nombre__icontains=palabra2) & models.Q(apellido__icontains=palabra1))
            )
        else:
            # Búsqueda con más de dos palabras: buscar cada una en cualquier campo
            query = models.Q()
            for palabra in palabras:
                query |= models.Q(nombre__icontains=palabra) | models.Q(apellido__icontains=palabra)
            usuarios = usuarios.filter(query)
    
    if email_filtro:
        usuarios = usuarios.filter(email__icontains=email_filtro)
    
    if telefono_filtro:
        usuarios = usuarios.filter(telefono__icontains=telefono_filtro)
    
    if estado_filtro:
        if estado_filtro == 'activo':
            usuarios = usuarios.filter(estado=True)
        elif estado_filtro == 'inactivo':
            usuarios = usuarios.filter(estado=False)
    
    if faltas_filtro:
        try:
            faltas_num = int(faltas_filtro)
            usuarios = usuarios.filter(contador_faltas__gte=faltas_num)
        except ValueError:
            pass
    
    # Ordenar por nombre y apellido
    usuarios = usuarios.order_by('nombre', 'apellido')
    
    # Estadísticas rápidas
    total_usuarios = Usuario.objects.count()
    usuarios_activos = Usuario.objects.filter(estado=True).count()
    usuarios_con_faltas = Usuario.objects.filter(contador_faltas__gt=0).count()
    
    context = {
        'usuarios': usuarios,
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'usuarios_con_faltas': usuarios_con_faltas,
        'filtros': {
            'nombre': nombre_filtro,
            'email': email_filtro,
            'telefono': telefono_filtro,
            'estado': estado_filtro,
            'faltas': faltas_filtro,
        }
    }
    
    return render(request, 'gestionar_usuarios.html', context)

@user_passes_test(lambda u: u.is_superuser)
def editar_usuario_admin(request, user_id):
    """Vista para que los administradores editen usuarios"""
    usuario_a_editar = get_object_or_404(Usuario, pk=user_id)
    
    if request.method == 'POST':
        # Actualizar datos básicos con formateo de nombres
        nombre_raw = request.POST.get('nombre', usuario_a_editar.nombre)
        apellido_raw = request.POST.get('apellido', usuario_a_editar.apellido)
        
        usuario_a_editar.nombre = formatear_nombre(nombre_raw)
        usuario_a_editar.apellido = formatear_nombre(apellido_raw)
        usuario_a_editar.email = request.POST.get('email', usuario_a_editar.email)
        usuario_a_editar.telefono = request.POST.get('telefono', usuario_a_editar.telefono)
        
        # Actualizar estado (habilitado/deshabilitado)
        estado = request.POST.get('estado')
        if estado == 'habilitado':
            usuario_a_editar.estado = True
        elif estado == 'deshabilitado':
            usuario_a_editar.estado = False
        
        # Actualizar contador de faltas
        try:
            faltas = int(request.POST.get('contador_faltas', usuario_a_editar.contador_faltas))
            usuario_a_editar.contador_faltas = max(0, faltas)  # No permitir valores negativos
        except (ValueError, TypeError):
            pass  # Mantener el valor actual si hay error
        
        # Procesar foto de perfil si se subió una nueva
        if 'foto_perfil' in request.FILES:
            usuario_a_editar.foto_perfil = request.FILES['foto_perfil']
        
        usuario_a_editar.save()
        messages.success(request, f'Usuario {usuario_a_editar.nombre} {usuario_a_editar.apellido} actualizado correctamente.')
        return redirect('gestionar-usuarios')
    
    context = {
        'usuario_editar': usuario_a_editar,
        'es_admin_editando': True
    }
    return render(request, 'editar_usuario_admin.html', context)

@login_required
def cambiar_contrasena(request):
    """Vista para cambiar contraseña del usuario desde su perfil"""
    if request.method == 'POST':
        form = CambiarContrasenaForm(request.user, request.POST)
        if form.is_valid():
            # Cambiar la contraseña
            nueva_contrasena = form.cleaned_data['nueva_contrasena']
            request.user.set_password(nueva_contrasena)
            request.user.save()
            
            # Actualizar la sesión para que no se deslogee
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            
            messages.success(request, '¡Contraseña cambiada exitosamente!')
            return redirect('perfil_usuario')
    else:
        form = CambiarContrasenaForm(request.user)
    
    return render(request, 'cambiar_contrasena.html', {'form': form})

@login_required
def cancelar_turno_usuario(request, turno_id):
    """Vista para que el usuario cancele su propio turno"""
    from turnos.models import Turno
    from turnos.views import crear_notificacion
    from django.utils import timezone
    from django.http import JsonResponse
    from datetime import timedelta
    
    try:
        turno = Turno.objects.get(
            id=turno_id,
            cliente=request.user,
            estado='ocupado',
            fecha_hora__gte=timezone.now()  # Solo turnos futuros
        )
        
        # Verificar si es una cancelación tardía (menos de 1 hora)
        ahora = timezone.now()
        tiempo_restante = turno.fecha_hora - ahora
        es_cancelacion_tardia = tiempo_restante <= timedelta(hours=1)
        
        # Si es por AJAX y es cancelación tardía, devolver advertencia
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and es_cancelacion_tardia:
            confirmar_con_falta = request.POST.get('confirmar_con_falta', 'false') == 'true'
            
            if not confirmar_con_falta:
                # Primera vez - mostrar advertencia
                horas_restantes = int(tiempo_restante.total_seconds() // 3600)
                minutos_restantes = int((tiempo_restante.total_seconds() % 3600) // 60)
                
                tiempo_texto = ""
                if horas_restantes > 0:
                    tiempo_texto = f"{horas_restantes} hora{'s' if horas_restantes != 1 else ''}"
                    if minutos_restantes > 0:
                        tiempo_texto += f" y {minutos_restantes} minuto{'s' if minutos_restantes != 1 else ''}"
                else:
                    tiempo_texto = f"{minutos_restantes} minuto{'s' if minutos_restantes != 1 else ''}"
                
                return JsonResponse({
                    'warning': True,
                    'mensaje': f'⚠️ Tu turno es en {tiempo_texto}. Cancelar con menos de 1 hora de anticipación agregará una FALTA a tu cuenta.',
                    'faltas_actuales': request.user.contador_faltas,
                    'tiempo_restante': tiempo_texto
                })
        
        # Cancelar el turno
        turno.estado = 'cancelado'
        turno.save()
        
        # Si es cancelación tardía, agregar falta
        if es_cancelacion_tardia:
            request.user.contador_faltas += 1
            
            # Si llega a 3 faltas, deshabilitar usuario
            if request.user.contador_faltas >= 3:
                request.user.estado = False
                mensaje_falta = f'❌ Turno cancelado. Se agregó 1 FALTA a tu cuenta. Has alcanzado 3 FALTAS y tu usuario ha sido DESHABILITADO.'
            else:
                mensaje_falta = f'⚠️ Turno cancelado. Se agregó 1 FALTA por cancelación tardía. Faltas actuales: {request.user.contador_faltas}/3.'
            
            request.user.save()
            
            # Crear notificación para administradores
            crear_notificacion(turno, 'turno_cancelado')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'mensaje': mensaje_falta,
                    'usuario_deshabilitado': not request.user.estado,
                    'faltas': request.user.contador_faltas
                })
            else:
                messages.warning(request, mensaje_falta)
                return redirect('perfil_usuario')
        else:
            # Cancelación normal (con más de 1 hora de anticipación)
            crear_notificacion(turno, 'turno_cancelado')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'mensaje': f'Turno del {turno.fecha_hora.strftime("%d/%m/%Y a las %H:%M")} cancelado correctamente.'
                })
            else:
                messages.success(request, f'Turno del {turno.fecha_hora.strftime("%d/%m/%Y a las %H:%M")} cancelado correctamente.')
                return redirect('perfil_usuario')
            
    except Turno.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'No se encontró el turno o no tienes permisos para cancelarlo.'
            }, status=404)
        else:
            messages.error(request, 'No se encontró el turno o no tienes permisos para cancelarlo.')
            return redirect('perfil_usuario')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Ocurrió un error al cancelar el turno.'
            }, status=500)
        else:
            messages.error(request, 'Ocurrió un error al cancelar el turno.')
            return redirect('perfil_usuario')
