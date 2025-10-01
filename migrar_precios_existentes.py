#!/usr/bin/env python
"""
Script para migrar turnos existentes y asignar precio_final basado en el precio del servicio.
Solo se ejecuta una vez después de agregar el campo precio_final.
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/home/gonzalo/Escritorio/proyecto barberia cop')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BarberiaApp.settings')
django.setup()

from turnos.models import Turno

def migrar_precios_existentes():
    """Migrar turnos existentes que no tienen precio_final"""
    print("=== MIGRACIÓN DE PRECIOS EXISTENTES ===")
    
    # Buscar turnos que no tienen precio_final pero sí tienen servicio
    turnos_sin_precio = Turno.objects.filter(
        precio_final__isnull=True,
        servicio__isnull=False
    ).select_related('servicio')
    
    print(f"Turnos encontrados sin precio_final: {turnos_sin_precio.count()}")
    
    if turnos_sin_precio.count() == 0:
        print("✅ No hay turnos que requieran migración")
        return
    
    # Migrar los precios
    turnos_actualizados = 0
    for turno in turnos_sin_precio:
        if turno.servicio and turno.servicio.precio:
            turno.precio_final = turno.servicio.precio
            turno.save()
            turnos_actualizados += 1
            
            if turnos_actualizados <= 5:  # Mostrar los primeros 5 como ejemplo
                print(f"  - Turno {turno.id}: {turno.servicio.nombre} → ${turno.precio_final}")
    
    print(f"✅ Migración completada: {turnos_actualizados} turnos actualizados")
    
    # Verificar turnos sin servicio
    turnos_sin_servicio = Turno.objects.filter(
        precio_final__isnull=True,
        servicio__isnull=True
    ).count()
    
    if turnos_sin_servicio > 0:
        print(f"⚠️  {turnos_sin_servicio} turnos sin servicio asociado (precio_final = NULL)")

if __name__ == '__main__':
    migrar_precios_existentes()
