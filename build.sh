#!/usr/bin/env bash
# Build script para Render

set -o errexit  # Exit on error

# Actualizar pip y setuptools primero
pip install --upgrade pip setuptools wheel

# Instalar dependencias
pip install -r requirements.txt

# Recopilar archivos estáticos
python manage.py collectstatic --no-input

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario automáticamente
python manage.py create_superuser_auto

# Cargar datos iniciales (opcional)
# python manage.py loaddata fixtures/barberos_inicial.json
# python manage.py loaddata fixtures/servicios_inicial.json
# python manage.py loaddata fixtures/productos_inicial.json

echo "Build completed successfully!"
