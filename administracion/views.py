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
from usuarios.models import Barbero, Usuario
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.db.models import F, Q
from django.contrib import messages

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
        try:
            barberos_ids = request.POST.getlist('barberos')
            dia = request.POST.get('dia')
            hora_inicio = request.POST.get('hora_inicio')
            duracion = int(request.POST.get('duracion'))
            cantidad_turnos = int(request.POST.get('cantidad_turnos'))
            
            # Validaciones básicas
            if not barberos_ids or not dia or not hora_inicio:
                messages.error(request, 'Faltan datos obligatorios para crear los turnos.')
                return HttpResponseRedirect('/administracion/turnos/')
            
            # Obtener servicio por defecto
            servicio = Servicio.objects.first()
            if not servicio:
                messages.error(request, 'No hay servicios disponibles. Crea al menos un servicio primero.')
                return HttpResponseRedirect('/administracion/turnos/')
            
            from datetime import datetime, timedelta
            turnos_creados = 0
            turnos_duplicados = 0
            
            for barbero_id in barberos_ids:
                # Verificar que el barbero existe
                try:
                    barbero = Barbero.objects.get(id=barbero_id)
                except Barbero.DoesNotExist:
                    continue
                
                actual = datetime.strptime(f"{dia} {hora_inicio}", "%Y-%m-%d %H:%M")
                
                for i in range(cantidad_turnos):
                    # Verificar si ya existe un turno para este barbero en esta fecha/hora
                    turno_existente = Turno.objects.filter(
                        barbero_id=barbero_id,
                        fecha_hora=actual
                    ).exists()
                    
                    if not turno_existente:
                        Turno.objects.create(
                            barbero_id=barbero_id,
                            fecha_hora=actual,
                            estado='disponible',
                            servicio=servicio
                        )
                        turnos_creados += 1
                    else:
                        turnos_duplicados += 1
                    
                    actual += timedelta(minutes=duracion)
            
            # Mensajes informativos
            if turnos_creados > 0:
                messages.success(request, f'Se crearon {turnos_creados} turnos exitosamente.')
            if turnos_duplicados > 0:
                messages.warning(request, f'Se omitieron {turnos_duplicados} turnos que ya existían.')
                
        except Exception as e:
            messages.error(request, f'Error al crear turnos: {str(e)}')
        
        return HttpResponseRedirect('/administracion/turnos/')
    
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

@user_passes_test(lambda u: u.is_superuser)
def archivar_turnos_vista(request):
    """Vista para archivar turnos expirados desde la web"""
    from django.core.management import call_command
    from django.contrib import messages
    from django.shortcuts import redirect
    from io import StringIO
    import sys
    
    if request.method == 'POST':
        # Capturar la salida del comando
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()
        
        try:
            # Obtener parámetros del formulario
            dias = request.POST.get('dias', 30)
            estados_seleccionados = request.POST.getlist('estados')
            
            # Si no se seleccionó ningún estado, usar por defecto ocupado y completado
            if not estados_seleccionados:
                estados_seleccionados = ['ocupado', 'completado']
            
            # Ejecutar el comando con los parámetros correctos
            call_command('archivar_turnos', 
                        days=int(dias),
                        estados=estados_seleccionados)
            
            output = buffer.getvalue()
            messages.success(request, f'Turnos archivados exitosamente:\n{output}')
        except Exception as e:
            messages.error(request, f'Error al archivar turnos: {str(e)}')
        finally:
            sys.stdout = old_stdout
        
        return redirect('administracion-turnos')
    
    # Vista GET - mostrar estadísticas dinámicas
    from datetime import timedelta
    
    # Obtener parámetros de la URL (si vienen de un filtro previo)
    dias_solicitados = request.GET.get('dias', 30)
    try:
        dias_solicitados = int(dias_solicitados)
    except (ValueError, TypeError):
        dias_solicitados = 30
    
    estados_solicitados = request.GET.getlist('estados')
    if not estados_solicitados:
        # Por defecto: ocupados, completados y cancelados (excluir disponibles)
        estados_solicitados = ['ocupado', 'completado', 'cancelado']
    
    fecha_limite = timezone.now() - timedelta(days=dias_solicitados)
    
    # Usar la misma consulta que el comando de archivado
    turnos_expirados = Turno.objects.filter(
        fecha_hora__lt=fecha_limite,
        estado__in=estados_solicitados
    ).select_related('barbero', 'servicio', 'cliente')
    
    # Debug para comparar con el comando
    # print(f"DEBUG Vista Web - Días: {dias_solicitados}")
    # print(f"DEBUG Vista Web - Estados: {estados_solicitados}")
    # print(f"DEBUG Vista Web - Fecha límite: {fecha_limite}")
    # print(f"DEBUG Vista Web - Conteo: {turnos_expirados.count()}")
    
    context = {
        'turnos_expirados_count': turnos_expirados.count(),
        'fecha_limite': fecha_limite,
        'dias_por_defecto': dias_solicitados,
        'estados_seleccionados': estados_solicitados,
        'turnos_sample': turnos_expirados[:10],  # Muestra de 10 turnos
        'todos_los_estados': ['disponible', 'ocupado', 'cancelado', 'completado']
    }
    
    return render(request, 'archivar_turnos.html', context)

@user_passes_test(lambda u: u.is_superuser)
def listar_archivos_excel(request):
    """Vista para listar todos los archivos Excel de turnos archivados"""
    import os
    from datetime import datetime
    from django.conf import settings
    
    archivos_dir = os.path.join(settings.MEDIA_ROOT, 'archivos_turnos')
    archivos_info = []
    
    if os.path.exists(archivos_dir):
        # Obtener todos los archivos .xlsx
        archivos = [f for f in os.listdir(archivos_dir) if f.endswith('.xlsx')]
        
        for archivo in archivos:
            ruta_completa = os.path.join(archivos_dir, archivo)
            
            # Obtener información del archivo
            stat = os.stat(ruta_completa)
            fecha_creacion = datetime.fromtimestamp(stat.st_ctime)
            tamaño = stat.st_size
            
            # Determinar tipo de archivo
            if 'historial' in archivo.lower():
                tipo = 'Historial Maestro'
                descripcion = 'Archivo que contiene todos los turnos archivados históricamente'
            else:
                tipo = 'Archivo Individual'
                # Extraer información del nombre si sigue nuestro formato
                if '--' in archivo and archivo.count('--') >= 3:
                    partes = archivo.replace('.xlsx', '').split('--')
                    if len(partes) >= 4:
                        descripcion = f"Archivado el {partes[1]} a las {partes[2].replace('-', ':')} - {partes[3]}"
                    else:
                        descripcion = 'Archivo de archivado individual'
                else:
                    descripcion = 'Archivo de archivado individual (formato anterior)'
            
            archivos_info.append({
                'nombre': archivo,
                'ruta_relativa': f'archivos_turnos/{archivo}',
                'fecha_creacion': fecha_creacion,
                'tamaño': tamaño,
                'tamaño_mb': round(tamaño / (1024 * 1024), 2),
                'tipo': tipo,
                'descripcion': descripcion
            })
        
        # Ordenar por fecha de creación (más reciente primero)
        archivos_info.sort(key=lambda x: x['fecha_creacion'], reverse=True)
    
    context = {
        'archivos': archivos_info,
        'total_archivos': len(archivos_info)
    }
    
    return render(request, 'listar_archivos_excel.html', context)

@user_passes_test(lambda u: u.is_superuser)
def descargar_archivo_excel(request, nombre_archivo):
    """Vista para descargar un archivo Excel específico"""
    import os
    from django.http import FileResponse, Http404
    from django.conf import settings
    
    # Construir la ruta del archivo
    archivo_path = os.path.join(settings.MEDIA_ROOT, 'archivos_turnos', nombre_archivo)
    
    # Verificar que el archivo existe y es un Excel
    if not os.path.exists(archivo_path) or not nombre_archivo.endswith('.xlsx'):
        raise Http404("Archivo no encontrado")
    
    # Retornar el archivo como descarga
    response = FileResponse(
        open(archivo_path, 'rb'),
        as_attachment=True,
        filename=nombre_archivo,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    return response
