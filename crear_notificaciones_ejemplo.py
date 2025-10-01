#!/usr/bin/env python3
"""
Script para crear notificaciones de prueba
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BarberiaApp.settings')
django.setup()

from turnos.models import Turno, Notificacion
from turnos.views import crear_notificacion

# Obtener algunos turnos para crear notificaciones
turnos = Turno.objects.all()[:3]

for turno in turnos:
    # Crear notificación de prueba
    crear_notificacion(turno, 'turno_reservado')
    print(f'Notificación creada para turno {turno.id}')

# Mostrar notificaciones no leídas
notificaciones = Notificacion.objects.filter(leida=False)
print(f'\nNotificaciones no leídas: {notificaciones.count()}')

for notif in notificaciones[:5]:
    print(f'- ID: {notif.id} - {notif.get_tipo_display()} - {notif.fecha_creacion}')

print('\n✅ Ahora puedes probar el botón del ojo en el panel de administración')
