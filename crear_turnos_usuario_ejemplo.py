#!/usr/bin/env python
"""
Script de prueba para generar turnos de usuario
"""

import os
import django
from django.utils import timezone
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BarberiaApp.settings')
django.setup()

from turnos.models import Turno
from usuarios.models import Usuario, Barbero
from servicios.models import Servicio

def crear_turnos_usuario():
    """Crea algunos turnos de ejemplo para el usuario de prueba"""
    
    print("Creando turnos de usuario de ejemplo...")
    
    # Verificar si existen los datos necesarios
    barberos = Barbero.objects.all()
    usuarios = Usuario.objects.all()
    servicios = Servicio.objects.all()
    
    if not barberos.exists():
        print("❌ No hay barberos en el sistema.")
        print("   Crea algunos barberos primero desde el panel de administración.")
        return
    
    if not usuarios.exists():
        print("❌ No hay usuarios en el sistema.")
        print("   Crea algunos usuarios primero.")
        return
        
    if not servicios.exists():
        print("❌ No hay servicios en el sistema.")
        print("   Crea algunos servicios primero desde el panel de administración.")
        return
    
    # Tomar el primer usuario disponible (que no sea superuser)
    usuario_regular = usuarios.filter(is_superuser=False).first()
    if not usuario_regular:
        print("❌ No hay usuarios regulares en el sistema.")
        print("   Crea un usuario regular primero (no administrador).")
        return
        
    barbero = barberos.first()
    servicio = servicios.first()
    
    print(f"Creando turnos para el usuario: {usuario_regular.nombre} {usuario_regular.apellido}")
    
    # Crear turnos de ejemplo en el futuro
    now = timezone.now()
    
    turnos_creados = []
    
    # Turno 1 - Mañana
    turno1 = Turno.objects.create(
        cliente=usuario_regular,
        barbero=barbero,
        fecha_hora=now + timedelta(days=1, hours=10),  # Mañana a las 10:00
        estado='ocupado',
        servicio=servicio
    )
    turnos_creados.append(turno1)
    
    # Turno 2 - En 3 días
    if servicios.count() > 1:
        servicio2 = servicios.all()[1]
    else:
        servicio2 = servicio
        
    if barberos.count() > 1:
        barbero2 = barberos.all()[1]
    else:
        barbero2 = barbero
    
    turno2 = Turno.objects.create(
        cliente=usuario_regular,
        barbero=barbero2,
        fecha_hora=now + timedelta(days=3, hours=15),  # En 3 días a las 15:00
        estado='ocupado',
        servicio=servicio2
    )
    turnos_creados.append(turno2)
    
    # Turno 3 - La próxima semana
    turno3 = Turno.objects.create(
        cliente=usuario_regular,
        barbero=barbero,
        fecha_hora=now + timedelta(days=7, hours=12),  # Próxima semana a las 12:00
        estado='ocupado',
        servicio=servicio
    )
    turnos_creados.append(turno3)
    
    print(f"✅ Se crearon {len(turnos_creados)} turnos para {usuario_regular.nombre}:")
    for turno in turnos_creados:
        print(f"   - {turno.fecha_hora.strftime('%d/%m/%Y %H:%M')} con {turno.barbero.nombre} ({turno.servicio.nombre})")
    
    print(f"\n📋 Información del usuario:")
    print(f"   - Nombre: {usuario_regular.nombre} {usuario_regular.apellido}")
    print(f"   - Email: {usuario_regular.email}")
    print(f"   - Turnos activos: {Turno.objects.filter(cliente=usuario_regular, estado='ocupado').count()}")
    
    print(f"\n🔗 Para ver los turnos, inicia sesión con este usuario en: http://127.0.0.1:8001/login/")
    print(f"   Y luego ve a: http://127.0.0.1:8001/perfil/")

if __name__ == '__main__':
    crear_turnos_usuario()
