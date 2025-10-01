#!/usr/bin/env python
"""
Script para crear un escenario de prueba visual de la restricción semanal.
Crea un usuario con un turno activo para probar el flujo completo.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append('/home/gonzalo/Escritorio/proyecto barberia cop')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BarberiaApp.settings')
django.setup()

from usuarios.models import Usuario, Barbero
from servicios.models import Servicio
from turnos.models import Turno
from django.utils import timezone

def crear_escenario_prueba():
    """Crear un escenario realista para probar la restricción"""
    print("=== CREANDO ESCENARIO DE PRUEBA VISUAL ===")
    
    # Crear usuario de prueba
    try:
        usuario = Usuario.objects.get(email='demo@barberia.com')
        print(f"Usuario existente: {usuario.email}")
    except Usuario.DoesNotExist:
        usuario = Usuario.objects.create_user(
            email='demo@barberia.com',
            password='demo123',
            nombre='Juan',
            apellido='Pérez',
            telefono='123456789',
            fecha_nacimiento='1985-05-15'
        )
        print(f"Usuario creado: {usuario.email}")
    
    # Limpiar turnos existentes del usuario demo
    turnos_existentes = Turno.objects.filter(cliente=usuario)
    count = turnos_existentes.count()
    turnos_existentes.delete()
    print(f"Eliminados {count} turnos existentes del usuario demo")
    
    # Obtener barbero y servicio
    barbero = Barbero.objects.first()
    servicio = Servicio.objects.first()
    
    if not barbero or not servicio:
        print("ERROR: No hay barberos o servicios en la base de datos")
        return
    
    # Crear un turno activo para mañana a las 10:00
    fecha_manana = timezone.now().date() + timedelta(days=1)
    hora = timezone.now().time().replace(hour=10, minute=0, second=0, microsecond=0)
    fecha_hora = timezone.make_aware(datetime.combine(fecha_manana, hora))
    
    turno_activo = Turno.objects.create(
        cliente=usuario,
        barbero=barbero,
        servicio=servicio,
        fecha_hora=fecha_hora,
        estado='ocupado'
    )
    
    print(f"Turno activo creado:")
    print(f"  - Usuario: {usuario.nombre} {usuario.apellido}")
    print(f"  - Email: {usuario.email}")
    print(f"  - Fecha/Hora: {turno_activo.fecha_hora}")
    print(f"  - Barbero: {barbero.nombre}")
    print(f"  - Servicio: {servicio.nombre}")
    print(f"  - Estado: {turno_activo.estado}")
    
    # Crear algunos turnos disponibles para la misma semana
    for i in range(2, 6):  # Martes a viernes de la misma semana
        fecha_dia = fecha_manana + timedelta(days=i-1)
        for hora_num in [11, 14, 16]:
            hora_turno = timezone.now().time().replace(hour=hora_num, minute=0, second=0, microsecond=0)
            fecha_hora_turno = timezone.make_aware(datetime.combine(fecha_dia, hora_turno))
            
            Turno.objects.create(
                barbero=barbero,
                servicio=servicio,
                fecha_hora=fecha_hora_turno,
                estado='disponible'
            )
    
    print(f"\nTurnos disponibles creados para la misma semana")
    print(f"El usuario {usuario.email} NO debería poder reservar ninguno de estos")
    print(f"porque ya tiene un turno activo en esa semana.")
    
    print("\n=== INSTRUCCIONES PARA PRUEBA VISUAL ===")
    print("1. Ve a http://127.0.0.1:8000")
    print("2. Inicia sesión con:")
    print(f"   Email: {usuario.email}")
    print("   Contraseña: demo123")
    print("3. Ve a 'Reservar Turno' y trata de reservar un turno")
    print("4. Deberías ver el mensaje de error sobre la restricción semanal")
    print("5. Para verificar que funciona cuando no hay restricción:")
    print("   - Ve al admin panel")
    print("   - Cambia el estado del turno a 'completado'")
    print("   - Vuelve a intentar reservar - ahora debería funcionar")

if __name__ == '__main__':
    crear_escenario_prueba()
