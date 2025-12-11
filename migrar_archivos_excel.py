#!/usr/bin/env python
"""
Script para migrar archivos Excel locales a la base de datos
Soluciona el problema de archivos efímeros en Render
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BarberiaApp.settings')
django.setup()

def migrar_archivos_locales():
    """Migra archivos Excel del sistema de archivos a la base de datos"""
    
    print("🔄 MIGRACIÓN DE ARCHIVOS EXCEL A BASE DE DATOS")
    print("=" * 60)
    
    from administracion.models import ArchivoExcel
    from django.conf import settings
    import os
    from datetime import datetime
    
    # Directorio de archivos
    archivos_dir = os.path.join(settings.MEDIA_ROOT, 'archivos_turnos')
    
    if not os.path.exists(archivos_dir):
        print(f"❌ Directorio no existe: {archivos_dir}")
        return
    
    print(f"📁 Buscando archivos en: {archivos_dir}")
    
    # Buscar archivos Excel
    archivos_encontrados = []
    for archivo in os.listdir(archivos_dir):
        if archivo.endswith('.xlsx'):
            ruta_completa = os.path.join(archivos_dir, archivo)
            if os.path.isfile(ruta_completa):
                archivos_encontrados.append((archivo, ruta_completa))
    
    print(f"📊 Archivos encontrados: {len(archivos_encontrados)}")
    
    if not archivos_encontrados:
        print("✅ No hay archivos para migrar")
        return
    
    migrados = 0
    saltados = 0
    errores = 0
    
    for nombre_archivo, ruta_completa in archivos_encontrados:
        print(f"\n📄 Procesando: {nombre_archivo}")
        
        # Verificar si ya existe en BD
        if ArchivoExcel.objects.filter(nombre_archivo=nombre_archivo).exists():
            print(f"   ⏩ Ya existe en BD, saltando")
            saltados += 1
            continue
        
        try:
            # Leer archivo
            with open(ruta_completa, 'rb') as f:
                archivo_bytes = f.read()
            
            # Obtener información del archivo
            stat = os.stat(ruta_completa)
            fecha_creacion = datetime.fromtimestamp(stat.st_ctime)
            tamaño_bytes = len(archivo_bytes)
            
            print(f"   📏 Tamaño: {tamaño_bytes} bytes ({tamaño_bytes/1024:.1f} KB)")
            
            # Determinar tipo
            if 'historial' in nombre_archivo.lower():
                tipo_archivo = ArchivoExcel.TIPO_HISTORIAL
            else:
                tipo_archivo = ArchivoExcel.TIPO_INDIVIDUAL
            
            # Crear en BD usando el método from_file
            try:
                archivo_excel = ArchivoExcel.from_file(
                    ruta_completa,
                    tipo_archivo=tipo_archivo,
                    descripcion=f"Migrado automáticamente desde {ruta_completa}"
                )
                
                print(f"   ✅ Migrado exitosamente (ID: {archivo_excel.id})")
                migrados += 1
                
            except Exception as e:
                print(f"   ❌ Error creando en BD: {e}")
                
                # Fallback: crear manualmente
                import base64
                
                archivo_base64 = base64.b64encode(archivo_bytes).decode('utf-8')
                data_url = f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{archivo_base64}"
                
                archivo_excel = ArchivoExcel.objects.create(
                    nombre_archivo=nombre_archivo,
                    tipo_archivo=tipo_archivo,
                    descripcion=f"Migrado manualmente desde {ruta_completa}",
                    archivo_excel=data_url,
                    fecha_creacion=fecha_creacion,
                    tamaño_bytes=tamaño_bytes
                )
                
                print(f"   ✅ Migrado manualmente (ID: {archivo_excel.id})")
                migrados += 1
        
        except Exception as e:
            print(f"   ❌ Error procesando archivo: {e}")
            errores += 1
    
    print(f"\n" + "=" * 60)
    print(f"📊 RESUMEN DE MIGRACIÓN")
    print(f"=" * 60)
    print(f"✅ Migrados: {migrados}")
    print(f"⏩ Saltados (ya existían): {saltados}")
    print(f"❌ Errores: {errores}")
    print(f"📁 Total procesados: {len(archivos_encontrados)}")
    
    if migrados > 0:
        print(f"\n🎉 ¡Migración completada!")
        print(f"Los archivos migrados ahora están en la base de datos y")
        print(f"funcionarán correctamente en Render (sin archivos efímeros).")
        
        # Opcional: sugerir eliminar archivos locales
        print(f"\n💡 SUGERENCIA:")
        print(f"Puedes eliminar los archivos locales ya que están en BD:")
        for nombre_archivo, ruta_completa in archivos_encontrados:
            if ArchivoExcel.objects.filter(nombre_archivo=nombre_archivo).exists():
                print(f"   rm '{ruta_completa}'")
    
    return migrados, saltados, errores

def verificar_integridad():
    """Verifica que todos los archivos en BD sean válidos"""
    
    print(f"\n🔍 VERIFICACIÓN DE INTEGRIDAD")
    print("=" * 40)
    
    from administracion.models import ArchivoExcel
    
    archivos = ArchivoExcel.objects.all()
    print(f"📊 Verificando {archivos.count()} archivos...")
    
    validos = 0
    invalidos = 0
    
    for archivo in archivos:
        try:
            # Verificar métodos básicos
            tiene_archivo = archivo.has_archivo_excel()
            tamaño = archivo.get_tamaño_mb()
            descripcion = archivo.get_descripcion_completa()
            
            if tiene_archivo and tamaño > 0:
                print(f"   ✅ {archivo.nombre_archivo} - {tamaño} MB")
                validos += 1
            else:
                print(f"   ⚠️  {archivo.nombre_archivo} - Sin archivo válido")
                invalidos += 1
                
        except Exception as e:
            print(f"   ❌ {archivo.nombre_archivo} - Error: {e}")
            invalidos += 1
    
    print(f"\n📈 RESULTADO:")
    print(f"✅ Válidos: {validos}")
    print(f"❌ Inválidos: {invalidos}")
    
    return validos, invalidos

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--verificar':
        verificar_integridad()
    else:
        migrar_archivos_locales()
        verificar_integridad()
