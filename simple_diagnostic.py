import os
import sys
import django

# Configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barberia.settings')
django.setup()

from administracion.models import ArchivoExcel

# Realizar el diagnóstico
try:
    print("=== DIAGNÓSTICO DE ARCHIVOS EXCEL ===")
    total = ArchivoExcel.objects.count()
    print(f"Total de archivos en BD: {total}")
    
    if total == 0:
        print("❌ No hay archivos Excel en la base de datos local")
    else:
        print("\n=== ARCHIVOS ENCONTRADOS ===")
        for i, archivo in enumerate(ArchivoExcel.objects.all().order_by('-fecha_creacion'), 1):
            print(f"{i}. {archivo.nombre_archivo}")
            print(f"   📅 Creado: {archivo.fecha_creacion}")
            
            # Verificar contenido
            try:
                if hasattr(archivo, 'archivo_excel') and archivo.archivo_excel:
                    size_chars = len(str(archivo.archivo_excel))
                    print(f"   ✅ Contenido: {size_chars} caracteres")
                else:
                    print(f"   ❌ Sin contenido: archivo_excel está vacío o es None")
            except Exception as e:
                print(f"   ⚠️ Error verificando: {e}")
                
            print()
            
    print("=== RESULTADO ===")
    print("Este diagnóstico es para la base de datos LOCAL.")
    print("El problema puede ser que el archivo existe en producción pero no localmente.")
    print("O que se creó el registro pero sin el contenido del archivo.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
