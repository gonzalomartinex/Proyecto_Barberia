from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from .models import Usuario
from django.utils import timezone
from django.utils.timezone import localtime
from datetime import datetime, timedelta
from usuarios.models import Barbero, Usuario
from servicios.models import Servicio
from turnos.models import Turno
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
        turno.estado = estado
        turno.save()
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
    turno = get_object_or_404(Turno, id=turno_id, estado='disponible')
    servicios = Servicio.objects.all()
    if request.method == 'POST':
        # Validar que el usuario no tenga otro turno reservado ese día
        fecha_turno = turno.fecha_hora.date()
        ya_tiene = Turno.objects.filter(
            cliente=request.user,
            fecha_hora__date=fecha_turno,
            estado='ocupado'
        ).exists()
        if ya_tiene:
            messages.error(request, 'No puedes tener más de una reserva por día.')
            return redirect('turnos-agenda')
        servicio_id = request.POST.get('servicio')
        servicio = get_object_or_404(Servicio, id=servicio_id)
        turno.cliente = request.user
        turno.estado = 'ocupado'
        turno.servicio = servicio
        turno.save()
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
        messages.error(request, 'Tu usuario aún no está habilitado por la barbería. No puedes reservar turnos.')
        return redirect('inicio')
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
            'barbero_id': t.barbero.id,
            'servicio_id': t.servicio.id,
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
        ya_tiene = Turno.objects.filter(
            cliente=request.user,
            fecha_hora__date=fecha_turno,
            estado='ocupado'
        ).exists()
        if ya_tiene:
            messages.error(request, 'No puedes tener más de una reserva por día.')
            return redirect('reservar-turno-form')
        servicio = get_object_or_404(Servicio, id=servicio_id)
        turno.cliente = request.user
        turno.estado = 'ocupado'
        turno.servicio = servicio
        turno.save()
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
