#!/usr/bin/env python
"""
Script para completar la funcionalidad del perfil con historial de turnos
"""

import os
import django
from django.utils import timezone
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BarberiaApp.settings')
django.setup()

from turnos.models import Turno, Notificacion
from usuarios.models import Usuario, Barbero
from servicios.models import Servicio

def crear_historial_turnos():
    """Crea un historial completo de turnos para probar las estadísticas"""
    
    print("Creando historial completo de turnos...")
    
    # Obtener datos
    usuario_regular = Usuario.objects.filter(is_superuser=False).first()
    if not usuario_regular:
        print("❌ No hay usuarios regulares en el sistema.")
        return
        
    barberos = list(Barbero.objects.all())
    servicios = list(Servicio.objects.all())
    
    if not barberos or not servicios:
        print("❌ Faltan barberos o servicios en el sistema.")
        return
    
    now = timezone.now()
    
    print(f"Creando historial para: {usuario_regular.nombre} {usuario_regular.apellido}")
    
    # Crear turnos completados (en el pasado)
    turnos_completados = []
    for i in range(5):  # 5 turnos completados
        dias_pasados = 7 + (i * 5)  # Hace 1-4 semanas
        turno = Turno.objects.create(
            cliente=usuario_regular,
            barbero=barberos[i % len(barberos)],
            fecha_hora=now - timedelta(days=dias_pasados, hours=2),
            estado='completado',
            servicio=servicios[i % len(servicios)]
        )
        turnos_completados.append(turno)
        
        # Crear notificación
        Notificacion.objects.create(
            tipo='turno_completado',
            turno=turno,
            mensaje=f"Turno completado - {turno.fecha_hora.strftime('%d/%m/%Y %H:%M')}"
        )
    
    # Crear turnos cancelados (algunos en el pasado, algunos en el futuro)
    turnos_cancelados = []
    for i in range(2):  # 2 turnos cancelados
        if i == 0:
            # Uno cancelado en el pasado
            fecha = now - timedelta(days=3, hours=1)
        else:
            # Uno que fue cancelado para el futuro
            fecha = now + timedelta(days=2, hours=3)
            
        turno = Turno.objects.create(
            cliente=usuario_regular,
            barbero=barberos[i % len(barberos)],
            fecha_hora=fecha,
            estado='cancelado',
            servicio=servicios[i % len(servicios)]
        )
        turnos_cancelados.append(turno)
        
        # Crear notificación
        Notificacion.objects.create(
            tipo='turno_cancelado',
            turno=turno,
            mensaje=f"Turno cancelado - {turno.fecha_hora.strftime('%d/%m/%Y %H:%M')}"
        )
    
    # Resumen
    total_turnos = Turno.objects.filter(cliente=usuario_regular).count()
    activos = Turno.objects.filter(
        cliente=usuario_regular, 
        estado='ocupado',
        fecha_hora__gte=now
    ).count()
    completados = Turno.objects.filter(cliente=usuario_regular, estado='completado').count()
    cancelados = Turno.objects.filter(cliente=usuario_regular, estado='cancelado').count()
    
    print(f"\n✅ Historial creado exitosamente:")
    print(f"   📊 Estadísticas del usuario {usuario_regular.nombre}:")
    print(f"   - Total de turnos: {total_turnos}")
    print(f"   - Turnos activos: {activos}")
    print(f"   - Turnos completados: {completados}")
    print(f"   - Turnos cancelados: {cancelados}")
    
    print(f"\n🔔 Notificaciones generadas: {Notificacion.objects.count()}")
    
    print(f"\n🔗 Ahora puedes:")
    print(f"   1. Ver el perfil completo en: http://127.0.0.1:8001/perfil/")
    print(f"   2. Ver las notificaciones en el panel admin: http://127.0.0.1:8001/admin-panel/")
    print(f"   3. Probar la cancelación de turnos desde el perfil")

if __name__ == '__main__':
    crear_historial_turnos()
