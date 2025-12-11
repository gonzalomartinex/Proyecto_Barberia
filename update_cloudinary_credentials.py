#!/usr/bin/env python3
"""
Script para actualizar credenciales de Cloudinary
Ejecutar con: python update_cloudinary_credentials.py
"""

def update_env_file(cloud_name, api_key, api_secret):
    """Actualiza el archivo .env con las nuevas credenciales"""
    import os
    
    env_file = '.env'
    
    # Leer archivo actual
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Actualizar o agregar variables de Cloudinary
    cloudinary_vars = {
        'CLOUDINARY_CLOUD_NAME': cloud_name,
        'CLOUDINARY_API_KEY': api_key,
        'CLOUDINARY_API_SECRET': api_secret
    }
    
    updated_lines = []
    vars_found = set()
    
    for line in lines:
        updated = False
        for var, value in cloudinary_vars.items():
            if line.startswith(f'{var}='):
                updated_lines.append(f'{var}={value}\n')
                vars_found.add(var)
                updated = True
                break
        
        if not updated:
            updated_lines.append(line)
    
    # Agregar variables que no existían
    for var, value in cloudinary_vars.items():
        if var not in vars_found:
            updated_lines.append(f'{var}={value}\n')
    
    # Escribir archivo actualizado
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"✅ Archivo {env_file} actualizado")

def update_render_yaml(cloud_name, api_key, api_secret):
    """Actualiza render.yaml con las nuevas credenciales"""
    render_file = 'render.yaml'
    
    with open(render_file, 'r') as f:
        content = f.read()
    
    # Reemplazar valores de Cloudinary
    replacements = [
        ('CLOUDINARY_CLOUD_NAME\n        value: dfkhulbwf', f'CLOUDINARY_CLOUD_NAME\n        value: {cloud_name}'),
        ('CLOUDINARY_API_KEY\n        value: 857993365988948', f'CLOUDINARY_API_KEY\n        value: {api_key}'),
        ('CLOUDINARY_API_SECRET\n        value: ccEnjqy6Kj4UYri9U2fsl4gdDfl', f'CLOUDINARY_API_SECRET\n        value: {api_secret}')
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    with open(render_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Archivo {render_file} actualizado")

def test_credentials(cloud_name, api_key, api_secret):
    """Prueba las credenciales antes de guardar"""
    try:
        import cloudinary
        from cloudinary import api
        
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        
        result = api.ping()
        print(f"✅ Credenciales válidas: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Error con las credenciales: {e}")
        return False

def main():
    print("🔧 ACTUALIZADOR DE CREDENCIALES CLOUDINARY")
    print("=" * 50)
    
    print("\nVe a tu dashboard de Cloudinary:")
    print("https://cloudinary.com/console")
    print("\nEn la sección 'API Keys', copia las credenciales completas:")
    print()
    
    cloud_name = input("Cloud Name: ").strip()
    api_key = input("API Key: ").strip()
    api_secret = input("API Secret (completo): ").strip()
    
    print(f"\n📋 Credenciales ingresadas:")
    print(f"Cloud Name: {cloud_name}")
    print(f"API Key: {api_key}")
    print(f"API Secret: {api_secret[:8]}...{api_secret[-4:]}")
    
    print(f"\n🧪 Probando credenciales...")
    
    if test_credentials(cloud_name, api_key, api_secret):
        print(f"\n💾 Guardando credenciales...")
        update_env_file(cloud_name, api_key, api_secret)
        update_render_yaml(cloud_name, api_key, api_secret)
        
        print(f"\n✅ ¡CREDENCIALES ACTUALIZADAS!")
        print(f"\nPróximos pasos:")
        print(f"1. Reiniciar el servidor Django")
        print(f"2. Probar subir una imagen")
        print(f"3. Verificar en Cloudinary dashboard que la imagen aparezca")
        print(f"4. Hacer deploy a producción")
    else:
        print(f"\n❌ Las credenciales no son válidas. No se guardaron.")
        print(f"Verifica que estén completas y correctas.")

if __name__ == "__main__":
    main()
