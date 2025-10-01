#!/usr/bin/env python3
"""
Script para limpiar notificaciones problemáticas y crear nuevas
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BarberiaApp.settings')
django.setup()

from turnos.models import Turno, Notificacion
from turnos.views import crear_notificacion

def limpiar_y_crear_notificaciones():
    print("🧹 Limpiando notificaciones problemáticas...")
    
    # Eliminar notificaciones de turnos sin cliente o barbero
    notificaciones_problematicas = []
    
    for notificacion in Notificacion.objects.all():
        try:
            # Intentar acceder a los atributos que causan el error
            _ = notificacion.get_mensaje_completo()
        except AttributeError as e:
            print(f"❌ Notificación problemática encontrada: ID {notificacion.id} - Error: {e}")
            notificaciones_problematicas.append(notificacion)
    
    # Eliminar notificaciones problemáticas
    if notificaciones_problematicas:
        for notif in notificaciones_problematicas:
            print(f"🗑️  Eliminando notificación ID {notif.id}")
            notif.delete()
        print(f"✅ {len(notificaciones_problematicas)} notificaciones problemáticas eliminadas")
    else:
        print("✅ No se encontraron notificaciones problemáticas")
    
    # Crear notificaciones de prueba válidas
    print("\n📝 Creando notificaciones de prueba...")
    
    turnos_validos = Turno.objects.filter(
        cliente__isnull=False,
        barbero__isnull=False
    )[:3]
    
    if turnos_validos.exists():
        for turno in turnos_validos:
            try:
                crear_notificacion(turno, 'turno_reservado')
                print(f"✅ Notificación creada para turno {turno.id}")
            except Exception as e:
                print(f"❌ Error creando notificación para turno {turno.id}: {e}")
    else:
        print("⚠️  No hay turnos válidos para crear notificaciones")
    
    # Mostrar estado final
    notificaciones_no_leidas = Notificacion.objects.filter(leida=False)
    print(f"\n📊 Estado final:")
    print(f"   Notificaciones no leídas: {notificaciones_no_leidas.count()}")
    
    for notif in notificaciones_no_leidas[:5]:
        try:
            mensaje = notif.get_mensaje_completo()[:50] + "..."
            print(f"   • ID {notif.id}: {mensaje}")
        except Exception as e:
            print(f"   • ID {notif.id}: Error - {e}")
    
    print(f"\n🔗 Prueba el panel: http://127.0.0.1:8000/admin-panel/")

if __name__ == "__main__":
    limpiar_y_crear_notificaciones()
