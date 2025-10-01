#!/usr/bin/env python
"""
Script para validar que la restricción de 1 turno activo por semana funcione correctamente.
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
from turnos.views import usuario_tiene_turno_activo_semana, obtener_inicio_semana, obtener_fin_semana
from django.utils import timezone

def crear_datos_prueba():
    """Crear datos de prueba si no existen"""
    print("=== CREANDO DATOS DE PRUEBA ===")
    
    # Crear usuario de prueba
    try:
        usuario = Usuario.objects.get(email='test@test.com')
        print(f"Usuario existente: {usuario.email}")
    except Usuario.DoesNotExist:
        usuario = Usuario.objects.create_user(
            email='test@test.com',
            password='testpass123',
            nombre='Test',
            apellido='Usuario',
            telefono='123456789',
            fecha_nacimiento='1990-01-01'
        )
        print(f"Usuario creado: {usuario.email}")
    
    # Crear barbero de prueba
    try:
        barbero = Barbero.objects.first()
        if not barbero:
            barbero = Barbero.objects.create(
                nombre='Barbero Test',
                email='barbero@test.com',
                telefono='987654321'
            )
            print(f"Barbero creado: {barbero.nombre}")
        else:
            print(f"Barbero existente: {barbero.nombre}")
    except:
        print("Error creando barbero")
        return None, None, None
    
    # Crear servicio de prueba
    try:
        servicio = Servicio.objects.first()
        if not servicio:
            servicio = Servicio.objects.create(
                nombre='Corte Test',
                precio=15000,
                tiempo_estimado=30
            )
            print(f"Servicio creado: {servicio.nombre}")
        else:
            print(f"Servicio existente: {servicio.nombre}")
    except:
        print("Error creando servicio")
        return None, None, None
    
    return usuario, barbero, servicio

def limpiar_turnos_test():
    """Limpiar turnos de test anteriores"""
    print("\n=== LIMPIANDO TURNOS DE TEST ===")
    turnos_test = Turno.objects.filter(cliente__email='test@test.com')
    count = turnos_test.count()
    turnos_test.delete()
    print(f"Eliminados {count} turnos de test")

def test_restriccion_semanal():
    """Test principal de la restricción semanal"""
    print("\n=== TEST RESTRICCIÓN SEMANAL ===")
    
    usuario, barbero, servicio = crear_datos_prueba()
    if not all([usuario, barbero, servicio]):
        print("ERROR: No se pudieron crear los datos de prueba")
        return
    
    limpiar_turnos_test()
    
    # Fecha de referencia - mañana
    fecha_base = timezone.now().date() + timedelta(days=1)
    hora_base = timezone.now().time().replace(hour=10, minute=0, second=0, microsecond=0)
    fecha_hora_base = timezone.make_aware(datetime.combine(fecha_base, hora_base))
    
    print(f"Fecha base para test: {fecha_base}")
    print(f"Semana: {obtener_inicio_semana(fecha_base)} al {obtener_fin_semana(fecha_base)}")
    
    # TEST 1: Usuario sin turnos - debería poder reservar
    print("\n--- TEST 1: Usuario sin turnos ---")
    tiene_activo = usuario_tiene_turno_activo_semana(usuario, fecha_base)
    print(f"¿Tiene turno activo? {tiene_activo}")
    assert not tiene_activo, "ERROR: Usuario sin turnos no debería tener turnos activos"
    print("✓ PASÓ: Usuario sin turnos puede reservar")
    
    # Crear un turno ocupado (activo) en la semana
    turno1 = Turno.objects.create(
        cliente=usuario,
        barbero=barbero,
        servicio=servicio,
        fecha_hora=fecha_hora_base,
        estado='ocupado'
    )
    print(f"Turno creado: {turno1.fecha_hora} ({turno1.estado})")
    
    # TEST 2: Usuario con turno activo - no debería poder reservar otro
    print("\n--- TEST 2: Usuario con turno activo ---")
    tiene_activo = usuario_tiene_turno_activo_semana(usuario, fecha_base)
    print(f"¿Tiene turno activo? {tiene_activo}")
    assert tiene_activo, "ERROR: Usuario con turno ocupado debería tener turnos activos"
    print("✓ PASÓ: Usuario con turno activo no puede reservar otro")
    
    # TEST 3: Probar en otro día de la misma semana
    print("\n--- TEST 3: Otro día de la misma semana ---")
    fecha_mismo_semana = fecha_base + timedelta(days=2)
    print(f"Fecha en la misma semana: {fecha_mismo_semana}")
    tiene_activo = usuario_tiene_turno_activo_semana(usuario, fecha_mismo_semana)
    print(f"¿Tiene turno activo en la misma semana? {tiene_activo}")
    assert tiene_activo, "ERROR: Debería detectar turno activo en la misma semana"
    print("✓ PASÓ: Restricción funciona en toda la semana")
    
    # TEST 4: Cambiar estado a completado - debería poder reservar otro
    print("\n--- TEST 4: Turno completado ---")
    turno1.estado = 'completado'
    turno1.save()
    print(f"Estado del turno cambiado a: {turno1.estado}")
    
    tiene_activo = usuario_tiene_turno_activo_semana(usuario, fecha_base)
    print(f"¿Tiene turno activo después de completar? {tiene_activo}")
    assert not tiene_activo, "ERROR: Usuario con turno completado debería poder reservar otro"
    print("✓ PASÓ: Usuario puede reservar después de completar turno")
    
    # TEST 5: Probar en semana siguiente
    print("\n--- TEST 5: Semana siguiente ---")
    fecha_siguiente_semana = fecha_base + timedelta(days=7)
    print(f"Fecha en semana siguiente: {fecha_siguiente_semana}")
    print(f"Nueva semana: {obtener_inicio_semana(fecha_siguiente_semana)} al {obtener_fin_semana(fecha_siguiente_semana)}")
    
    # Volver a poner el turno como ocupado
    turno1.estado = 'ocupado'
    turno1.save()
    
    tiene_activo = usuario_tiene_turno_activo_semana(usuario, fecha_siguiente_semana)
    print(f"¿Tiene turno activo en semana siguiente? {tiene_activo}")
    assert not tiene_activo, "ERROR: Restricción no debería aplicar a otra semana"
    print("✓ PASÓ: Restricción no afecta otras semanas")
    
    print("\n=== TODOS LOS TESTS PASARON CORRECTAMENTE ===")
    print("La restricción de 1 turno activo por semana está funcionando bien.")

if __name__ == '__main__':
    try:
        test_restriccion_semanal()
    except Exception as e:
        print(f"\nERROR EN EL TEST: {e}")
        import traceback
        traceback.print_exc()
