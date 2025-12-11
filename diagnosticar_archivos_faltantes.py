#!/usr/bin/env python
"""
Script para diagnosticar archivos Excel faltantes o con problemas
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/home/gonzalo/Escritorio/proyecto barberia cop')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barberia.settings')
django.setup()

from administracion.models import ArchivoExcel
from django.utils import timezone

def diagnosticar_archivos():
    print("=== DIAGNÓSTICO DE ARCHIVOS EXCEL ===")
    print(f"Fecha de diagnóstico: {timezone.now()}")
    print()
    
    # Contar total de archivos
    total_archivos = ArchivoExcel.objects.count()
    print(f"Total de archivos en BD: {total_archivos}")
    
    if total_archivos == 0:
        print("❌ No hay archivos Excel en la base de datos")
        return
    
    print()
    print("=== ANÁLISIS INDIVIDUAL DE ARCHIVOS ===")
    
    archivos_ok = 0
    archivos_sin_contenido = 0
    archivos_problema = 0
    
    for i, archivo in enumerate(ArchivoExcel.objects.all().order_by('-fecha_creacion'), 1):
        print(f"\n{i}. Archivo: {archivo.nombre_archivo}")
        print(f"   📅 Creado: {archivo.fecha_creacion}")
        print(f"   👤 Creado por: {archivo.usuario.username if archivo.usuario else 'Sin usuario'}")
        
        # Verificar contenido
        try:
            if hasattr(archivo, 'archivo_excel') and archivo.archivo_excel:
                size_mb = len(archivo.archivo_excel) / 1024 / 1024
                print(f"   ✅ Contenido: {len(archivo.archivo_excel)} bytes ({size_mb:.2f} MB)")
                archivos_ok += 1
            else:
                print(f"   ❌ Sin contenido: archivo_excel es None o vacío")
                archivos_sin_contenido += 1
        except Exception as e:
            print(f"   ⚠️  Error verificando contenido: {e}")
            archivos_problema += 1
        
        # Verificar método has_archivo_excel
        try:
            tiene_archivo = archivo.has_archivo_excel()
            print(f"   📊 has_archivo_excel(): {tiene_archivo}")
        except Exception as e:
            print(f"   ⚠️  Error en has_archivo_excel(): {e}")
            archivos_problema += 1
    
    print()
    print("=== RESUMEN ===")
    print(f"✅ Archivos OK: {archivos_ok}")
    print(f"❌ Archivos sin contenido: {archivos_sin_contenido}")
    print(f"⚠️  Archivos con problemas: {archivos_problema}")
    
    if archivos_sin_contenido > 0:
        print()
        print("🔧 ARCHIVOS PROBLEMÁTICOS:")
        for archivo in ArchivoExcel.objects.all():
            if not archivo.has_archivo_excel():
                print(f"   - {archivo.nombre_archivo} (creado: {archivo.fecha_creacion})")
        
        print()
        print("💡 RECOMENDACIONES:")
        print("1. Estos archivos aparecen en la lista pero no se pueden descargar")
        print("2. Eliminar archivos sin contenido:")
        print("   ArchivoExcel.objects.filter(archivo_excel__isnull=True).delete()")
        print("3. O recrear los archivos Excel faltantes")

if __name__ == "__main__":
    diagnosticar_archivos()
