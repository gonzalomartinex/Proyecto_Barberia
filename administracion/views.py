from django.shortcuts import render
from rest_framework import generics, permissions
from .models import RegistroServicios
from .serializers import RegistroServiciosSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.db.models import Count, Sum
from servicios.models import Servicio
from turnos.models import Turno
from usuarios.models import Barbero
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.db.models import F, Q

# Create your views here.

class RegistroServiciosListCreateView(generics.ListCreateAPIView):
    queryset = RegistroServicios.objects.all()
    serializer_class = RegistroServiciosSerializer
    permission_classes = [permissions.IsAuthenticated]

class RegistroServiciosRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = RegistroServicios.objects.all()
    serializer_class = RegistroServiciosSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['GET'])
@permission_classes([IsAdminUser])
def estadisticas_servicios_mas_pedidos(request):
    data = (Turno.objects.values('servicio__nombre')
            .annotate(total=Count('servicio'))
            .order_by('-total')[:5])
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def estadisticas_ingresos_por_barbero(request):
    data = (Turno.objects.filter(estado='completado')
            .values('barbero__nombre')
            .annotate(ingresos=Sum('servicio__precio'))
            .order_by('-ingresos'))
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def estadisticas_cantidad_turnos(request):
    barbero = request.GET.get('barbero')
    servicio = request.GET.get('servicio')
    turnos = Turno.objects.all()
    if barbero:
        turnos = turnos.filter(barbero__id=barbero)
    if servicio:
        turnos = turnos.filter(servicio__id=servicio)
    total = turnos.count()
    return Response({'total_turnos': total})

@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
def administracion_turnos(request):
    barberos = Barbero.objects.all()
    hoy = timezone.localdate()
    turnos = Turno.objects.all().select_related('barbero', 'servicio').order_by('fecha_hora')
    # Filtros
    barbero_id = request.GET.get('barbero')
    dia = request.GET.get('dia')
    hora_inicio_h = request.GET.get('hora_inicio_h')
    hora_inicio_m = request.GET.get('hora_inicio_m')
    hora_fin_h = request.GET.get('hora_fin_h')
    hora_fin_m = request.GET.get('hora_fin_m')
    estado = request.GET.get('estado')
    # Si viene desde el GET tradicional (ej: recarga), parsear
    if not hora_inicio_h and request.GET.get('hora_inicio'):
        partes = request.GET['hora_inicio'].split(':')
        if len(partes) == 2:
            hora_inicio_h, hora_inicio_m = partes
    if not hora_fin_h and request.GET.get('hora_fin'):
        partes = request.GET['hora_fin'].split(':')
        if len(partes) == 2:
            hora_fin_h, hora_fin_m = partes
    hora_inicio = f"{hora_inicio_h}:{hora_inicio_m}" if hora_inicio_h and hora_inicio_m else None
    hora_fin = f"{hora_fin_h}:{hora_fin_m}" if hora_fin_h and hora_fin_m else None
    from datetime import datetime, timedelta, timezone as dt_timezone
    tz = timezone.get_current_timezone()
    if barbero_id:
        turnos = turnos.filter(barbero__id=barbero_id)
    if dia:
        # Usar replace(tzinfo=tz) y convertir a UTC con .astimezone(dt_timezone.utc)
        inicio = datetime.strptime(f"{dia} 00:00", "%Y-%m-%d %H:%M").replace(tzinfo=tz).astimezone(dt_timezone.utc)
        fin = datetime.strptime(f"{dia} 23:59:59", "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz).astimezone(dt_timezone.utc)
        if hora_inicio and hora_fin:
            inicio = datetime.strptime(f"{dia} {hora_inicio}", "%Y-%m-%d %H:%M").replace(tzinfo=tz).astimezone(dt_timezone.utc)
            fin = datetime.strptime(f"{dia} {hora_fin}", "%Y-%m-%d %H:%M").replace(tzinfo=tz).astimezone(dt_timezone.utc)
        elif hora_inicio:
            inicio = datetime.strptime(f"{dia} {hora_inicio}", "%Y-%m-%d %H:%M").replace(tzinfo=tz).astimezone(dt_timezone.utc)
        elif hora_fin:
            fin = datetime.strptime(f"{dia} {hora_fin}", "%Y-%m-%d %H:%M").replace(tzinfo=tz).astimezone(dt_timezone.utc)
        turnos = turnos.filter(fecha_hora__gte=inicio, fecha_hora__lte=fin)
    elif hora_inicio or hora_fin:
        # Filtrar por hora local manualmente en Python
        from django.utils.timezone import localtime
        h_ini, m_ini = (int(hora_inicio.split(':')[0]), int(hora_inicio.split(':')[1])) if hora_inicio else (None, None)
        h_fin, m_fin = (int(hora_fin.split(':')[0]), int(hora_fin.split(':')[1])) if hora_fin else (None, None)
        turnos = list(turnos)
        turnos_filtrados = []
        for t in turnos:
            fh_local = localtime(t.fecha_hora)
            h = fh_local.hour
            m = fh_local.minute
            if hora_inicio and hora_fin:
                if (h > h_ini or (h == h_ini and m >= m_ini)) and (h < h_fin or (h == h_fin and m <= m_fin)):
                    turnos_filtrados.append(t)
            elif hora_inicio:
                if (h > h_ini or (h == h_ini and m >= m_ini)):
                    turnos_filtrados.append(t)
            elif hora_fin:
                if (h < h_fin or (h == h_fin and m <= m_fin)):
                    turnos_filtrados.append(t)
        turnos = turnos_filtrados
    if isinstance(turnos, list):
        if estado:
            turnos = [t for t in turnos if t.estado == estado]
    else:
        if estado:
            turnos = turnos.filter(estado=estado)
    horas = [f'{h:02d}' for h in range(0, 24)]
    minutos = [f'{m:02d}' for m in range(0, 60, 5)]
    return render(request, 'administracion_turnos.html', {
        'barberos': barberos,
        'turnos': turnos,
        'hoy': hoy,
        'horas': horas,
        'minutos': minutos,
        'hora_inicio_h': hora_inicio_h,
        'hora_inicio_m': hora_inicio_m,
        'hora_fin_h': hora_fin_h,
        'hora_fin_m': hora_fin_m,
    })

@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
@csrf_exempt
def agregar_turnos(request):
    if request.method == 'POST':
        barberos_ids = request.POST.getlist('barberos')
        dia = request.POST.get('dia')
        hora_inicio = request.POST.get('hora_inicio')
        duracion = int(request.POST.get('duracion'))
        cantidad_turnos = int(request.POST.get('cantidad_turnos'))
        servicio = Servicio.objects.first()  # Por defecto, asignar el primer servicio (puedes ajustar esto)
        from datetime import datetime, timedelta
        for barbero_id in barberos_ids:
            actual = datetime.strptime(f"{dia} {hora_inicio}", "%Y-%m-%d %H:%M")
            for i in range(cantidad_turnos):
                Turno.objects.create(
                    barbero_id=barbero_id,
                    fecha_hora=actual,
                    estado='disponible',
                    servicio=servicio
                )
                actual += timedelta(minutes=duracion)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/administracion/turnos/'))
    return HttpResponseRedirect('/administracion/turnos/')

@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
@require_POST
def cancelar_turno_admin(request):
    turno_id = request.POST.get('turno_id')
    if turno_id:
        from turnos.models import Turno
        turno = Turno.objects.filter(id=turno_id).first()
        if turno and turno.estado != 'cancelado':
            turno.estado = 'cancelado'
            turno.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/administracion/turnos/'))

@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
@require_POST
def cambiar_estado_turno_admin(request):
    turno_id = request.POST.get('turno_id')
    nuevo_estado = request.POST.get('estado')
    if turno_id and nuevo_estado:
        from turnos.models import Turno
        turno = Turno.objects.filter(id=turno_id).first()
        if turno and turno.estado != nuevo_estado:
            turno.estado = nuevo_estado
            turno.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/administracion/turnos/'))
