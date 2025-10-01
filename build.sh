#!/usr/bin/env bash
# Build script para Render

set -o errexit  # Exit on error

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Recopilar archivos estáticos
python manage.py collectstatic --no-input

# Ejecutar migraciones
python manage.py migrate

# Cargar datos iniciales (opcional)
# python manage.py loaddata fixtures/barberos_inicial.json
# python manage.py loaddata fixtures/servicios_inicial.json
# python manage.py loaddata fixtures/productos_inicial.json

echo "Build completed successfully!"
