#!/usr/bin/env python3
"""
Script para listar imágenes en Cloudinary
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BarberiaApp.settings')
django.setup()

# Verificar si Cloudinary está configurado
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

if not all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET]):
    print("❌ Cloudinary no configurado localmente")
    print("🔗 Para ver las imágenes, ve al dashboard de Cloudinary:")
    print(f"   https://console.cloudinary.com/console")
    print("   Luego busca 'Media Library' en el menú izquierdo")
    sys.exit(1)

try:
    import cloudinary
    import cloudinary.api
    
    # Configurar Cloudinary
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True
    )
    
    print(f"🔍 Buscando imágenes en Cloudinary: {CLOUDINARY_CLOUD_NAME}")
    print("=" * 60)
    
    # Listar todas las imágenes
    try:
        result = cloudinary.api.resources(max_results=50, resource_type="image")
        
        if result['resources']:
            print(f"📷 Encontradas {len(result['resources'])} imágenes:")
            print()
            
            for resource in result['resources']:
                print(f"📁 {resource['public_id']}")
                print(f"   📏 {resource['width']}x{resource['height']} pixels")
                print(f"   📅 Subida: {resource['created_at'][:10]}")
                print(f"   🔗 URL: {resource['secure_url']}")
                print()
        else:
            print("📭 No se encontraron imágenes en Cloudinary")
            
    except Exception as e:
        print(f"❌ Error al listar imágenes: {e}")
        
except ImportError:
    print("❌ Cloudinary no está instalado")
    
except Exception as e:
    print(f"❌ Error de configuración: {e}")
