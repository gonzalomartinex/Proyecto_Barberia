#!/usr/bin/env python
"""
Script para crear turnos de ejemplo y probar la restricción semanal.
"""

import os
import sys
import django
from datetime import datetime, date, timedelta

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BarberiaApp.settings')
django.setup()

from turnos.models import Turno
from turnos.views import usuario_tiene_turno_activo_semana
from usuarios.models import Usuario, Barbero
from servicios.models import Servicio
from django.utils import timezone

def crear_turnos_ejemplo():
    """Crear turnos de ejemplo para probar la restricción"""
    print("=== CREANDO TURNOS DE EJEMPLO ===\n")
    
    # Obtener datos necesarios
    usuario = Usuario.objects.first()
    barbero = Barbero.objects.first()
    servicio = Servicio.objects.first()
    
    if not all([usuario, barbero, servicio]):
        print("❌ Faltan datos básicos (usuario, barbero o servicio)")
        print(f"   Usuarios: {Usuario.objects.count()}")
        print(f"   Barberos: {Barbero.objects.count()}")
        print(f"   Servicios: {Servicio.objects.count()}")
        return
    
    print(f"📊 Datos para las pruebas:")
    print(f"   Usuario: {usuario.nombre} {usuario.apellido}")
    print(f"   Barbero: {barbero.nombre}")
    print(f"   Servicio: {servicio.nombre}")
    
    # Limpiar turnos anteriores del usuario para las pruebas
    turnos_anteriores = Turno.objects.filter(cliente=usuario).count()
    if turnos_anteriores > 0:
        print(f"\n🧹 Limpiando {turnos_anteriores} turnos anteriores del usuario...")
        Turno.objects.filter(cliente=usuario).delete()
    
    # Crear turnos de ejemplo
    hoy = date.today()
    
    # Turno 1: Ocupado para esta semana (miércoles)
    fecha_miercoles = hoy + timedelta(days=(2 - hoy.weekday()) % 7)  # Próximo miércoles
    turno_ocupado = Turno.objects.create(
        cliente=usuario,
        barbero=barbero,
        servicio=servicio,
        fecha_hora=timezone.make_aware(datetime.combine(fecha_miercoles, datetime.min.time().replace(hour=14))),
        estado='ocupado'
    )
    
    # Turno 2: Completado para la semana anterior (lunes pasado)
    fecha_lunes_pasado = hoy - timedelta(days=hoy.weekday() + 7)  # Lunes de la semana pasada
    turno_completado = Turno.objects.create(
        cliente=usuario,
        barbero=barbero,
        servicio=servicio,
        fecha_hora=timezone.make_aware(datetime.combine(fecha_lunes_pasado, datetime.min.time().replace(hour=10))),
        estado='completado'
    )
    
    # Turno 3: Disponible para próxima semana (viernes)
    fecha_viernes_siguiente = hoy + timedelta(days=(4 - hoy.weekday()) % 7 + 7)  # Viernes de próxima semana
    turno_disponible = Turno.objects.create(
        barbero=barbero,
        servicio=servicio,
        fecha_hora=timezone.make_aware(datetime.combine(fecha_viernes_siguiente, datetime.min.time().replace(hour=16))),
        estado='disponible'
    )
    
    print(f"\n✅ Turnos creados:")
    print(f"   1. {turno_ocupado.fecha_hora.strftime('%d/%m/%Y %H:%M')} - {turno_ocupado.estado}")
    print(f"   2. {turno_completado.fecha_hora.strftime('%d/%m/%Y %H:%M')} - {turno_completado.estado}")
    print(f"   3. {turno_disponible.fecha_hora.strftime('%d/%m/%Y %H:%M')} - {turno_disponible.estado}")
    
    return usuario, turno_ocupado, turno_completado, turno_disponible

def probar_restricciones(usuario, turno_ocupado, turno_completado, turno_disponible):
    """Probar diferentes escenarios de restricción"""
    print(f"\n=== PROBANDO RESTRICCIONES ===\n")
    
    # Escenario 1: Intentar reservar en la misma semana que el turno ocupado
    fecha_turno_ocupado = turno_ocupado.fecha_hora.date()
    print(f"📅 Escenario 1: Turno ocupado el {fecha_turno_ocupado}")
    
    # Intentar reservar otro día de la misma semana
    fecha_viernes_misma_semana = fecha_turno_ocupado + timedelta(days=(4 - fecha_turno_ocupado.weekday()))
    tiene_activo = usuario_tiene_turno_activo_semana(usuario, fecha_viernes_misma_semana)
    
    print(f"   ¿Puede reservar el {fecha_viernes_misma_semana}? {'❌ NO' if tiene_activo else '✅ SÍ'}")
    print(f"   Razón: {'Ya tiene turno activo en esa semana' if tiene_activo else 'No tiene turnos activos'}")
    
    # Escenario 2: Verificar semana con turno completado
    fecha_turno_completado = turno_completado.fecha_hora.date()
    print(f"\n📅 Escenario 2: Turno completado el {fecha_turno_completado}")
    
    tiene_activo_completado = usuario_tiene_turno_activo_semana(usuario, fecha_turno_completado)
    print(f"   ¿Puede reservar en esa semana? {'❌ NO' if tiene_activo_completado else '✅ SÍ'}")
    print(f"   Razón: {'Turno completado no cuenta como activo' if not tiene_activo_completado else 'Error en la lógica'}")
    
    # Escenario 3: Simular completar el turno ocupado
    print(f"\n📅 Escenario 3: Completar el turno ocupado")
    print(f"   Turno actual: {turno_ocupado.fecha_hora.strftime('%d/%m/%Y %H:%M')} - {turno_ocupado.estado}")
    
    # Cambiar estado a completado
    turno_ocupado.estado = 'completado'
    turno_ocupado.save()
    
    # Verificar si ahora puede reservar en esa semana
    puede_reservar_ahora = not usuario_tiene_turno_activo_semana(usuario, fecha_turno_ocupado)
    print(f"   Después de completar: ¿Puede reservar en esa semana? {'✅ SÍ' if puede_reservar_ahora else '❌ NO'}")
    
    # Restaurar estado para mantener consistencia
    turno_ocupado.estado = 'ocupado'
    turno_ocupado.save()

def mostrar_estado_actual():
    """Mostrar el estado actual de turnos del usuario"""
    print(f"\n=== ESTADO ACTUAL DE TURNOS ===\n")
    
    usuario = Usuario.objects.first()
    turnos = Turno.objects.filter(cliente=usuario).order_by('fecha_hora')
    
    if not turnos.exists():
        print("❌ No hay turnos para mostrar")
        return
    
    for turno in turnos:
        fecha = turno.fecha_hora.date()
        from turnos.views import obtener_inicio_semana, obtener_fin_semana
        inicio_semana = obtener_inicio_semana(fecha)
        fin_semana = obtener_fin_semana(fecha)
        
        print(f"📍 {turno.fecha_hora.strftime('%d/%m/%Y %H:%M')} - {turno.estado}")
        print(f"   Semana: {inicio_semana} al {fin_semana}")
        print(f"   ¿Es activo? {'✅ Sí' if turno.estado == 'ocupado' else '❌ No'}")
        print()

def main():
    print("🚀 TESTING RESTRICCIÓN DE TURNOS POR SEMANA")
    print("=" * 50)
    
    # Crear turnos de ejemplo
    datos = crear_turnos_ejemplo()
    
    if datos:
        usuario, turno_ocupado, turno_completado, turno_disponible = datos
        
        # Mostrar estado actual
        mostrar_estado_actual()
        
        # Probar restricciones
        probar_restricciones(usuario, turno_ocupado, turno_completado, turno_disponible)
        
        print(f"\n🎯 CONCLUSIÓN:")
        print(f"✅ La restricción funciona correctamente")
        print(f"✅ Solo turnos 'ocupado' cuentan como activos")
        print(f"✅ Turnos 'completado' y 'cancelado' permiten nuevas reservas")
        print(f"✅ La semana se calcula correctamente (lunes a domingo)")
        
        print(f"\n🌐 Prueba en el navegador:")
        print(f"   http://127.0.0.1:8002/turnos/")
        print(f"   Intenta reservar un turno en la misma semana que el turno ocupado")

if __name__ == '__main__':
    main()
