#!/usr/bin/env python3

import sqlite3
import os
from datetime import datetime

# Ruta a la base de datos
db_path = "/home/gonzalo/Escritorio/proyecto barberia cop/db.sqlite3"

def diagnosticar_archivos_sql():
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    print("=== DIAGNÓSTICO DE ARCHIVOS EXCEL (SQL DIRECTO) ===")
    print(f"Archivo BD: {db_path}")
    print(f"Fecha: {datetime.now()}")
    print()
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='administracion_archivoexcel'
        """)
        
        if not cursor.fetchone():
            print("❌ Tabla 'administracion_archivoexcel' no existe")
            conn.close()
            return
        
        # Contar total de registros
        cursor.execute("SELECT COUNT(*) FROM administracion_archivoexcel")
        total = cursor.fetchone()[0]
        print(f"Total de archivos en BD: {total}")
        
        if total == 0:
            print("❌ No hay archivos Excel en la base de datos")
            conn.close()
            return
        
        # Obtener información detallada
        cursor.execute("""
            SELECT 
                id, 
                nombre_archivo, 
                fecha_creacion, 
                tipo_archivo,
                CASE 
                    WHEN archivo_excel IS NULL THEN 'NULL'
                    WHEN archivo_excel = '' THEN 'VACÍO'
                    ELSE LENGTH(archivo_excel) || ' chars'
                END as estado_archivo
            FROM administracion_archivoexcel 
            ORDER BY fecha_creacion DESC
        """)
        
        archivos = cursor.fetchall()
        
        print()
        print("=== ARCHIVOS ENCONTRADOS ===")
        archivos_ok = 0
        archivos_problema = 0
        
        for i, (id_archivo, nombre, fecha, tipo, estado) in enumerate(archivos, 1):
            print(f"{i}. {nombre}")
            print(f"   📅 Creado: {fecha}")
            print(f"   🏷️  Tipo: {tipo}")
            print(f"   📊 Estado: {estado}")
            
            if estado in ['NULL', 'VACÍO']:
                print(f"   ❌ PROBLEMA: Sin contenido")
                archivos_problema += 1
            else:
                print(f"   ✅ OK: Tiene contenido")
                archivos_ok += 1
            print()
        
        print("=== RESUMEN ===")
        print(f"✅ Archivos OK: {archivos_ok}")
        print(f"❌ Archivos problemáticos: {archivos_problema}")
        
        if archivos_problema > 0:
            print()
            print("🔧 ARCHIVOS PROBLEMÁTICOS:")
            cursor.execute("""
                SELECT nombre_archivo, fecha_creacion 
                FROM administracion_archivoexcel 
                WHERE archivo_excel IS NULL OR archivo_excel = ''
                ORDER BY fecha_creacion DESC
            """)
            problematicos = cursor.fetchall()
            for nombre, fecha in problematicos:
                print(f"   - {nombre} (creado: {fecha})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error accediendo a la base de datos: {e}")

if __name__ == "__main__":
    diagnosticar_archivos_sql()
