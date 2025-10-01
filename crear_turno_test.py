#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BarberiaApp.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from usuarios.models import Usuario
from turnos.models import Turno
from usuarios.models import Barbero
from servicios.models import Servicio

usuario = Usuario.objects.filter(is_superuser=False, estado=True).first()
barbero = Barbero.objects.first()
servicio = Servicio.objects.first()

fecha_turno = timezone.now() + timedelta(minutes=30)

turno = Turno.objects.create(
    cliente=usuario, 
    barbero=barbero, 
    servicio=servicio, 
    fecha_hora=fecha_turno, 
    estado='ocupado'
)

print(f'Turno creado: ID {turno.id}')
print(f'Usuario: {usuario.email}')
print(f'Fecha: {fecha_turno.strftime("%d/%m/%Y %H:%M")}')
print('⚠️ CANCELACIÓN TARDÍA (30 minutos)')
