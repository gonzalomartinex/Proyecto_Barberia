from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from .models import Usuario
from django.utils import timezone
from django.utils.timezone import localtime
from datetime import datetime, timedelta
from usuarios.models import Barbero, Usuario
from servicios.models import Servicio
from turnos.models import Turno, Notificacion
from django.contrib.auth.decorators import login_required
from rest_framework import generics, permissions
from .serializers import TurnoSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
import json
from decimal import Decimal
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
import pytz

def obtener_inicio_semana(fecha):
    """
    Obtiene el primer día (lunes) de la semana que contiene la fecha dada.
    """
    dias_desde_lunes = fecha.weekday()  # 0 = lunes, 6 = domingo
    inicio_semana = fecha - timedelta(days=dias_desde_lunes)
    return inicio_semana

def obtener_fin_semana(fecha):
    """
    Obtiene el último día (domingo) de la semana que contiene la fecha dada.
    """
    inicio_semana = obtener_inicio_semana(fecha)
    fin_semana = inicio_semana + timedelta(days=6)  # 6 días después del lunes
    return fin_semana

def usuario_tiene_turno_activo_semana(usuario, fecha):
    """
    Verifica si el usuario tiene algún turno activo en la semana de la fecha dada.
    Turnos activos = ocupado (no incluye completado, cancelado)
    """
    inicio_semana = obtener_inicio_semana(fecha)
    fin_semana = obtener_fin_semana(fecha)
    
    # Convertir a datetime para la consulta
    from django.utils import timezone
    inicio_datetime = timezone.make_aware(datetime.combine(inicio_semana, datetime.min.time()))
    fin_datetime = timezone.make_aware(datetime.combine(fin_semana, datetime.max.time()))
    
    turnos_activos = Turno.objects.filter(
        cliente=usuario,
        fecha_hora__range=[inicio_datetime, fin_datetime],
        estado='ocupado'  # Solo turnos ocupados (activos)
    )
    
    return turnos_activos.exists()

# Create your views here.

class TurnoListCreateView(generics.ListCreateAPIView):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    permission_classes = [permissions.IsAuthenticated]

class TurnoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['POST'])
@permission_classes([IsAdminUser])
def cambiar_estado_turno(request, pk):
    try:
        turno = Turno.objects.get(pk=pk)
    except Turno.DoesNotExist:
        return Response({'error': 'Turno no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    estado = request.data.get('estado')
    if estado in dict(Turno.ESTADO_CHOICES):
        old_estado = turno.estado
        turno.estado = estado
        turno.save()
        
        # Crear notificación automática si el estado cambió
        if old_estado != estado:
            if estado == 'cancelado':
                crear_notificacion(turno, 'turno_cancelado')
            elif estado == 'completado':
                crear_notificacion(turno, 'turno_completado')
        
        return Response({'success': True, 'estado': turno.estado})
    return Response({'error': 'Debe enviar un estado válido'}, status=status.HTTP_400_BAD_REQUEST)

@login_required
def turnos_agenda(request):
    barberos = Barbero.objects.all()
    semana_actual = request.GET.get('semana') or timezone.now().strftime('%Y-W%W')
    barbero_id = request.GET.get('barbero')
    # Calcular rango de la semana en zona local
    try:
        year, week = map(int, semana_actual.split('-W'))
        primer_dia = datetime.strptime(f'{year}-W{week}-1', "%Y-W%W-%w")
        primer_dia = timezone.make_aware(primer_dia, timezone.get_current_timezone())
    except Exception:
        primer_dia = timezone.localtime(timezone.now()).replace(hour=0, minute=0, second=0, microsecond=0)
    ultimo_dia = primer_dia + timedelta(days=6)
    turnos = Turno.objects.filter(fecha_hora__range=[primer_dia, ultimo_dia])
    if barbero_id:
        turnos = turnos.filter(barbero__id=barbero_id)
    turnos = turnos.select_related('barbero', 'servicio').order_by('fecha_hora')
    # Convertir a hora local para mostrar
    for t in turnos:
        t.fecha_hora = localtime(t.fecha_hora)
    return render(request, 'turnos.html', {
        'barberos': barberos,
        'turnos': turnos,
        'semana_actual': semana_actual,
        'request': request,
    })

@login_required
def reservar_turno(request, turno_id):
    # Verificar si el usuario está habilitado
    if not request.user.estado:
        messages.error(request, 'Tu usuario está deshabilitado. No puedes reservar turnos. Contacta con la barbería para reactivar tu cuenta.')
        return redirect('perfil_usuario')
    
    turno = get_object_or_404(Turno, id=turno_id, estado='disponible')
    servicios = Servicio.objects.all()
    
    if request.method == 'POST':
        # Nueva validación: verificar que no tenga más de un turno activo por semana
        fecha_turno = turno.fecha_hora.date()
        
        if usuario_tiene_turno_activo_semana(request.user, fecha_turno):
            inicio_semana = obtener_inicio_semana(fecha_turno)
            fin_semana = obtener_fin_semana(fecha_turno)
            
            messages.error(request, 
                f'Ya tienes un turno activo en la semana del {inicio_semana.strftime("%d/%m")} al {fin_semana.strftime("%d/%m/%Y")}. '
                f'Solo puedes tener un turno activo por semana. Una vez que se complete tu turno actual, '
                f'podrás reservar otro en esa misma semana.'
            )
            return redirect('turnos-agenda')
        
        # Validación adicional: no más de una reserva por día (mantener la existente)
        ya_tiene_ese_dia = Turno.objects.filter(
            cliente=request.user,
            fecha_hora__date=fecha_turno,
            estado='ocupado'
        ).exists()
        
        if ya_tiene_ese_dia:
            messages.error(request, 'No puedes tener más de una reserva por día.')
            return redirect('turnos-agenda')
        
        # Si pasó todas las validaciones, proceder con la reserva
        servicio_id = request.POST.get('servicio')
        servicio = get_object_or_404(Servicio, id=servicio_id)
        turno.cliente = request.user
        turno.estado = 'ocupado'
        turno.servicio = servicio
        turno.precio_final = servicio.precio  # Guardar el precio del servicio
        turno.save()
        
        # Crear notificación
        crear_notificacion(turno, 'turno_reservado')
        
        messages.success(request, '¡Turno reservado exitosamente!')
        return redirect('inicio')
    
    return render(request, 'confirmar_reserva_turno.html', {
        'turno': turno,
        'servicios': servicios,
    })

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

@login_required
def reservar_turno_form(request):
    if not request.user.estado:
        messages.error(request, 'Tu usuario está deshabilitado. No puedes reservar turnos online. Contacta con la barbería para reactivar tu cuenta.')
        return redirect('perfil_usuario')
    servicios = list(Servicio.objects.all().values('id', 'nombre', 'precio'))
    barberos = list(Barbero.objects.all().values('id', 'nombre'))
    # Obtener todos los turnos disponibles próximos (solo los disponibles)
    turnos = Turno.objects.filter(estado='disponible').select_related('servicio', 'barbero')
    # Agrupar turnos por día y hora local
    turnos_por_dia = {}
    for t in turnos:
        fecha_local = localtime(t.fecha_hora)
        fecha = fecha_local.date().isoformat()
        hora = fecha_local.strftime('%H:%M')
        if fecha not in turnos_por_dia:
            turnos_por_dia[fecha] = {}
        if hora not in turnos_por_dia[fecha]:
            turnos_por_dia[fecha][hora] = []
        turnos_por_dia[fecha][hora].append({
            'id': t.id,
            'barbero_id': t.barbero.id if t.barbero else None,
            'servicio_id': t.servicio.id if t.servicio else None,
        })
    if request.method == 'POST':
        servicio_id = request.POST.get('servicio')
        turno_id = request.POST.get('turno_id')
        barbero_id = request.POST.get('barbero_id')
        if not (servicio_id and turno_id and barbero_id):
            messages.error(request, 'Debes seleccionar servicio, turno y barbero.')
            return redirect('reservar-turno-form')
        turno = get_object_or_404(Turno, id=turno_id, estado='disponible', barbero_id=barbero_id)
        fecha_turno = localtime(turno.fecha_hora).date()
        
        # Nueva validación: verificar que no tenga más de un turno activo por semana
        tiene_activo = usuario_tiene_turno_activo_semana(request.user, fecha_turno)
        
        if tiene_activo:
            inicio_semana = obtener_inicio_semana(fecha_turno)
            fin_semana = obtener_fin_semana(fecha_turno)
            
            messages.error(request, 
                f'Ya tienes un turno activo en la semana del {inicio_semana.strftime("%d/%m")} al {fin_semana.strftime("%d/%m/%Y")}. '
                f'Solo puedes tener un turno activo por semana. Una vez que se complete tu turno actual, '
                f'podrás reservar otro en esa misma semana.'
            )
            return redirect('reservar-turno-form')
        
        # Validación adicional: no más de una reserva por día (mantener la existente)
        ya_tiene_ese_dia = Turno.objects.filter(
            cliente=request.user,
            fecha_hora__date=fecha_turno,
            estado='ocupado'
        ).exists()
        
        if ya_tiene_ese_dia:
            messages.error(request, 'No puedes tener más de una reserva por día.')
            return redirect('reservar-turno-form')
        servicio = get_object_or_404(Servicio, id=servicio_id)
        turno.cliente = request.user
        turno.estado = 'ocupado'
        turno.servicio = servicio
        turno.precio_final = servicio.precio  # Guardar el precio del servicio
        turno.save()
        
        # Crear notificación automática
        crear_notificacion(turno, 'turno_reservado')
        
        messages.success(request, '¡Turno reservado exitosamente!')
        return redirect('inicio')
    return render(request, 'turnos_reserva_form.html', {
        'servicios_json': json.dumps(servicios, cls=DecimalEncoder),
        'turnos_json': json.dumps(turnos_por_dia),
        'barberos_json': json.dumps(barberos),
    })

@login_required
def perfil_usuario(request):
    # Aquí iría la lógica de la vista de perfil de usuario
    return render(request, 'perfil.html')

def crear_notificacion(turno, tipo):
    """Función auxiliar para crear notificaciones automáticamente"""
    try:
        Notificacion.objects.create(
            tipo=tipo,
            turno=turno,
            mensaje=f"{tipo.replace('_', ' ').title()} - {turno.fecha_hora.strftime('%d/%m/%Y %H:%M')}"
        )
    except Exception as e:
        print(f"Error creando notificación: {e}")

@login_required
def marcar_notificacion_leida(request, notificacion_id):
    """Marca una notificación como leída"""
    # Verificar que sea usuario admin
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Permisos insuficientes'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
        
    try:
        notificacion = Notificacion.objects.get(id=notificacion_id)
        notificacion.leida = True
        notificacion.save()
        return JsonResponse({'success': True, 'mensaje': 'Notificación marcada como leída'})
    except Notificacion.DoesNotExist:
        return JsonResponse({'error': 'Notificación no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def obtener_notificaciones_recientes():
    """Obtiene las notificaciones más recientes para el panel de administración"""
    # Obtener las últimas 10 notificaciones no leídas
    notificaciones_recientes = Notificacion.objects.filter(leida=False)[:10]
    return notificaciones_recientes

@user_passes_test(lambda u: u.is_superuser)
def listar_notificaciones(request):
    """Vista para mostrar todas las notificaciones con filtros y paginación"""
    
    # Obtener todas las notificaciones ordenadas por fecha
    notificaciones = Notificacion.objects.all().order_by('-fecha_creacion')
    
    # Filtros
    estado_filtro = request.GET.get('estado', '')  # leidas, no_leidas, todas
    tipo_filtro = request.GET.get('tipo', '')
    buscar = request.GET.get('buscar', '')
    
    # Aplicar filtro de estado
    if estado_filtro == 'leidas':
        notificaciones = notificaciones.filter(leida=True)
    elif estado_filtro == 'no_leidas':
        notificaciones = notificaciones.filter(leida=False)
    # Si es 'todas' o vacío, no filtramos por estado
    
    # Aplicar filtro de tipo
    if tipo_filtro:
        notificaciones = notificaciones.filter(tipo=tipo_filtro)
    
    # Aplicar búsqueda en el mensaje
    if buscar:
        notificaciones = notificaciones.filter(
            Q(mensaje__icontains=buscar) |
            Q(turno__cliente__nombre__icontains=buscar) |
            Q(turno__cliente__apellido__icontains=buscar) |
            Q(turno__barbero__nombre__icontains=buscar)
        )
    
    # Paginación
    paginator = Paginator(notificaciones, 15)  # 15 notificaciones por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_notificaciones = Notificacion.objects.count()
    no_leidas = Notificacion.objects.filter(leida=False).count()
    leidas = Notificacion.objects.filter(leida=True).count()
    
    # Tipos disponibles para el filtro
    tipos_disponibles = Notificacion.TIPO_CHOICES
    
    context = {
        'page_obj': page_obj,
        'total_notificaciones': total_notificaciones,
        'no_leidas': no_leidas,
        'leidas': leidas,
        'tipos_disponibles': tipos_disponibles,
        'filtros': {
            'estado': estado_filtro,
            'tipo': tipo_filtro,
            'buscar': buscar,
        }
    }
    
    return render(request, 'listar_notificaciones.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def actualizar_precio_turno(request):
    """Vista AJAX para actualizar el precio final de un turno"""
    if request.method == 'POST':
        try:
            turno_id = request.POST.get('turno_id')
            nuevo_precio = request.POST.get('precio')
            
            turno = get_object_or_404(Turno, id=turno_id)
            turno.precio_final = nuevo_precio
            turno.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Precio actualizado correctamente',
                'nuevo_precio': float(turno.precio_final)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar precio: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def obtener_datos_turno(request, turno_id):
    """Vista AJAX para obtener datos de un turno específico"""
    try:
        turno = get_object_or_404(Turno, id=turno_id)
        
        # Convertir a hora local para mostrar en el formulario
        from django.utils.timezone import localtime
        fecha_hora_local = localtime(turno.fecha_hora)
        
        datos = {
            'id': turno.id,
            'fecha': fecha_hora_local.strftime('%Y-%m-%d'),
            'hora': fecha_hora_local.strftime('%H:%M'),
            'barbero_id': turno.barbero.id if turno.barbero else None,
            'servicio_id': turno.servicio.id if turno.servicio else None,
            'estado': turno.estado,
            'precio_final': float(turno.precio_final) if turno.precio_final else None,
            'cliente_email': turno.cliente.email if turno.cliente else None,
        }
        
        return JsonResponse({
            'success': True,
            'turno': datos
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener datos: {str(e)}'
        })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def editar_turno(request):
    """Vista AJAX para editar un turno completo"""
    if request.method == 'POST':
        try:
            turno_id = request.POST.get('turno_id')
            turno = get_object_or_404(Turno, id=turno_id)
            
            # Actualizar fecha y hora solo si realmente cambió
            fecha = request.POST.get('fecha')
            hora = request.POST.get('hora')
            if fecha and hora:
                from django.utils.timezone import localtime
                import pytz
                
                # Obtener fecha/hora actual del turno en local
                fecha_hora_actual_local = localtime(turno.fecha_hora)
                fecha_actual = fecha_hora_actual_local.strftime('%Y-%m-%d')
                hora_actual = fecha_hora_actual_local.strftime('%H:%M')
                
                # Solo actualizar si hay cambio real en fecha o hora
                if fecha != fecha_actual or hora != hora_actual:
                    # Parsear la nueva fecha/hora como naive
                    fecha_hora_str = f"{fecha} {hora}"
                    fecha_hora_naive = datetime.strptime(fecha_hora_str, '%Y-%m-%d %H:%M')
                    
                    # Obtener la zona horaria local (Argentina)
                    tz_local = pytz.timezone('America/Argentina/Buenos_Aires')
                    
                    # Localizar en zona horaria argentina (sin conversión)
                    fecha_hora_nueva = tz_local.localize(fecha_hora_naive)
                    
                    turno.fecha_hora = fecha_hora_nueva
            
            # Actualizar barbero
            barbero_id = request.POST.get('barbero')
            if barbero_id:
                from usuarios.models import Barbero
                barbero = get_object_or_404(Barbero, id=barbero_id)
                turno.barbero = barbero
            
            # Actualizar servicio (puede ser NULL)
            servicio_id = request.POST.get('servicio')
            if servicio_id:
                from servicios.models import Servicio
                servicio = get_object_or_404(Servicio, id=servicio_id)
                turno.servicio = servicio
            else:
                turno.servicio = None
            
            # Actualizar estado
            estado = request.POST.get('estado')
            if estado:
                turno.estado = estado
            
            # Actualizar precio final
            precio_final = request.POST.get('precio_final')
            if precio_final:
                turno.precio_final = precio_final
            else:
                turno.precio_final = None
            
            # Actualizar cliente
            cliente_email = request.POST.get('cliente_email')
            if cliente_email:
                try:
                    cliente = Usuario.objects.get(email=cliente_email)
                    turno.cliente = cliente
                except Usuario.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': f'No se encontró usuario con email: {cliente_email}'
                    })
            else:
                turno.cliente = None
            
            turno.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Turno actualizado correctamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar turno: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def marcar_todas_notificaciones_leidas(request):
    """Marca todas las notificaciones no leídas como leídas"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener todas las notificaciones no leídas
        notificaciones_no_leidas = Notificacion.objects.filter(leida=False)
        count = notificaciones_no_leidas.count()
        
        # Marcar todas como leídas
        notificaciones_no_leidas.update(leida=True)
        
        return JsonResponse({
            'success': True, 
            'mensaje': f'{count} notificaciones marcadas como leídas',
            'count': count
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
