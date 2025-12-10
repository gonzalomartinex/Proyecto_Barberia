from django.shortcuts import render, get_object_or_404
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
from django.http import HttpResponseRedirect, JsonResponse
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
    
    # Obtener servicios para el modal de edición
    from servicios.models import Servicio
    servicios = Servicio.objects.all()
    
    return render(request, 'administracion_turnos.html', {
        'barberos': barberos,
        'servicios': servicios,
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
            
            # Ya no necesitamos servicio por defecto - los turnos se crean sin servicio
            
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
                            servicio=None  # Los turnos se crean sin servicio
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
            
            # Si es una petición AJAX, responder con JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'nuevo_estado': nuevo_estado,
                    'turno_id': turno_id
                })
    
    # Para peticiones normales (no AJAX), mantener el redirect
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
            
            # Si no se seleccionó ningún estado, usar por defecto ocupado, completado y expirado
            if not estados_seleccionados:
                estados_seleccionados = ['ocupado', 'completado', 'expirado']
            
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
        # Por defecto: ocupados, completados, cancelados y expirados (excluir disponibles)
        estados_solicitados = ['ocupado', 'completado', 'cancelado', 'expirado']
    
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
        'todos_los_estados': ['disponible', 'ocupado', 'cancelado', 'completado', 'expirado']
    }
    
    return render(request, 'archivar_turnos.html', context)

@user_passes_test(lambda u: u.is_superuser)
def listar_archivos_excel(request):
    """Vista para listar todos los archivos Excel de turnos archivados desde la base de datos"""
    from administracion.models import ArchivoExcel
    
    # Obtener archivos desde la base de datos
    archivos_bd = ArchivoExcel.objects.all().order_by('-fecha_creacion')
    
    # Convertir a formato compatible con la plantilla
    archivos_info = []
    
    for archivo in archivos_bd:
        archivos_info.append({
            'id': archivo.id,
            'nombre': archivo.nombre_archivo,
            'fecha_creacion': archivo.fecha_creacion,
            'tamaño': archivo.tamaño_bytes,
            'tamaño_mb': archivo.get_tamaño_mb(),
            'tipo': archivo.get_tipo_archivo_display(),
            'descripcion': archivo.descripcion or archivo.get_descripcion_completa(),
            'cantidad_turnos': archivo.cantidad_turnos,
            'periodo_inicio': archivo.fecha_periodo_inicio,
            'periodo_fin': archivo.fecha_periodo_fin,
            'version': archivo.version,
            'tiene_archivo': archivo.has_archivo_excel(),
        })
    
    # También obtener archivos locales si existen (para compatibilidad durante la transición)
    import os
    from datetime import datetime
    from django.conf import settings
    
    archivos_dir = os.path.join(settings.MEDIA_ROOT, 'archivos_turnos')
    archivos_locales = []
    
    if os.path.exists(archivos_dir):
        archivos = [f for f in os.listdir(archivos_dir) if f.endswith('.xlsx')]
        
        for archivo in archivos:
            # Verificar si ya está en BD
            if not ArchivoExcel.objects.filter(nombre_archivo=archivo).exists():
                ruta_completa = os.path.join(archivos_dir, archivo)
                stat = os.stat(ruta_completa)
                fecha_creacion = datetime.fromtimestamp(stat.st_ctime)
                
                archivos_locales.append({
                    'nombre': archivo,
                    'ruta_relativa': f'archivos_turnos/{archivo}',
                    'fecha_creacion': fecha_creacion,
                    'tamaño': stat.st_size,
                    'tamaño_mb': round(stat.st_size / (1024 * 1024), 2),
                    'tipo': 'Historial Maestro' if 'historial' in archivo.lower() else 'Archivo Individual',
                    'descripcion': 'Archivo local (no migrado a BD)',
                    'es_local': True,
                })
    
    context = {
        'archivos': archivos_info,
        'archivos_locales': archivos_locales,
        'total_archivos': len(archivos_info),
        'total_locales': len(archivos_locales),
    }
    
    return render(request, 'listar_archivos_excel.html', context)

@user_passes_test(lambda u: u.is_superuser)
def descargar_archivo_excel(request, nombre_archivo):
    """Vista para descargar un archivo Excel específico desde la base de datos o archivos locales"""
    from django.http import Http404
    from administracion.models import ArchivoExcel
    
    # Primero intentar desde la base de datos
    try:
        archivo_bd = ArchivoExcel.objects.get(nombre_archivo=nombre_archivo)
        if archivo_bd.has_archivo_excel():
            return archivo_bd.descargar_como_response()
    except ArchivoExcel.DoesNotExist:
        pass
    
    # Si no está en BD, intentar desde archivos locales (fallback)
    import os
    from django.http import FileResponse
    from django.conf import settings
    
    archivo_path = os.path.join(settings.MEDIA_ROOT, 'archivos_turnos', nombre_archivo)
    
    if os.path.exists(archivo_path) and nombre_archivo.endswith('.xlsx'):
        # Retornar el archivo local como descarga
        response = FileResponse(
            open(archivo_path, 'rb'),
            as_attachment=True,
        filename=nombre_archivo,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    return response

@user_passes_test(lambda u: u.is_superuser)
def obtener_datos_turno_admin(request, turno_id):
    """Vista AJAX para obtener datos de un turno específico desde administración"""
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

@user_passes_test(lambda u: u.is_superuser)
def editar_turno_admin(request):
    """Vista AJAX para editar un turno completo desde administración"""
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
                    from datetime import datetime
                    
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
                    from usuarios.models import Usuario
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
