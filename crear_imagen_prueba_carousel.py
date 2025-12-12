#!/usr/bin/env python
"""
Crear imagen de prueba en el carrusel para probar eliminación automática de Cloudinary
"""
import os
import sys
import django
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BarberiaApp.settings')
django.setup()

from BarberiaApp.models import CarouselImage
from django.db import models

def crear_imagen_prueba_carousel():
    """Crea una imagen de prueba en el carrusel usando una imagen existente"""
    
    print("🎠 CREANDO IMAGEN DE PRUEBA EN EL CARRUSEL")
    print("=" * 50)
    
    # Buscar una imagen que sepamos que funciona
    imagenes_prueba = [
        "/home/gonzalo/Escritorio/proyecto barberia cop/media/barberos/trabajos/cortebarba.png",
        "/home/gonzalo/Escritorio/proyecto barberia cop/media/barberos/trabajos/cortepelo.png",
        "/home/gonzalo/Escritorio/proyecto barberia cop/media/barberos/trabajos/a.png"
    ]
    
    imagen_seleccionada = None
    for ruta in imagenes_prueba:
        if os.path.exists(ruta):
            imagen_seleccionada = ruta
            print(f"✅ Imagen encontrada: {os.path.basename(ruta)}")
            break
    
    if not imagen_seleccionada:
        print("❌ No se encontraron imágenes de prueba")
        return None
    
    try:
        # Obtener el próximo número de orden
        ultimo_orden = CarouselImage.objects.aggregate(
            max_orden=models.Max('orden')
        )['max_orden'] or 0
        
        nuevo_orden = ultimo_orden + 1
        
        # Abrir archivo de imagen
        with open(imagen_seleccionada, 'rb') as f:
            # Crear archivo Django
            archivo_django = SimpleUploadedFile(
                name=f"prueba_cloudinary_{nuevo_orden}.png",
                content=f.read(),
                content_type='image/png'
            )
            
            # Crear registro en el carrusel
            nueva_imagen = CarouselImage.objects.create(
                imagen=archivo_django,
                orden=nuevo_orden
            )
            
            print(f"🎉 Imagen creada exitosamente:")
            print(f"   ID: {nueva_imagen.id}")
            print(f"   Orden: {nueva_imagen.orden}")
            print(f"   Archivo: {nueva_imagen.imagen.name}")
            print(f"   URL: {nueva_imagen.imagen.url}")
            
            # Verificar si se subió a Cloudinary
            if 'cloudinary.com' in nueva_imagen.imagen.url:
                print("✅ Imagen subida a Cloudinary - perfecta para probar eliminación automática")
            else:
                print("ℹ️  Imagen guardada localmente")
            
            return nueva_imagen
            
    except Exception as e:
        print(f"❌ Error creando imagen de prueba: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    
    print("🧪 CREADOR DE IMAGEN DE PRUEBA PARA CARRUSEL")
    print("=" * 60)
    
    # Listar imágenes actuales
    imagenes_actuales = CarouselImage.objects.count()
    print(f"📊 Imágenes actuales en el carrusel: {imagenes_actuales}")
    
    if imagenes_actuales > 0:
        respuesta = input("🤔 Ya hay imágenes en el carrusel. ¿Crear una más? (s/n): ").strip().lower()
        if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Operación cancelada")
            return
    
    # Crear imagen de prueba
    imagen_creada = crear_imagen_prueba_carousel()
    
    if imagen_creada:
        print(f"\n✅ ¡Listo! Imagen de prueba creada.")
        print(f"🔧 Ahora puedes:")
        print(f"   1. Ver la imagen en: http://127.0.0.1:8001/admin/BarberiaApp/carouselimage/")
        print(f"   2. Eliminarla desde el admin para probar la limpieza automática de Cloudinary")
        print(f"   3. O ejecutar el script de prueba: python test_carousel_cloudinary_cleanup.py")
    else:
        print("❌ No se pudo crear la imagen de prueba")

if __name__ == '__main__':
    main()
