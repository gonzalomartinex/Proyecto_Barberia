#!/usr/bin/env bash
# Build script para Render

set -o errexit  # Exit on error

# Actualizar pip y setuptools primero
pip install --upgrade pip setuptools wheel

# Instalar dependencias
pip install -r requirements.txt

# Recopilar archivos estáticos
python manage.py collectstatic --no-input

# Copiar archivos media a static para que WhiteNoise los sirva
python manage.py copy_media_to_static

# Ejecutar migraciones
python manage.py migrate

# Diagnóstico de Cloudinary
python manage.py diagnosticar_cloudinary

# Verificar usuarios existentes
python manage.py verify_users

# Crear superusuario automáticamente
python manage.py create_superuser_auto

# Verificar usuarios después de la creación
python manage.py verify_users

# Cargar datos iniciales (opcional)
# python manage.py loaddata fixtures/barberos_inicial.json
# python manage.py loaddata fixtures/servicios_inicial.json
# python manage.py loaddata fixtures/productos_inicial.json

echo "Build completed successfully!"
