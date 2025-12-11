#!/bin/bash

# Configurar variables de entorno Cloudinary localmente
echo "🔧 Configurando variables de entorno Cloudinary localmente..."

# Exportar las variables de entorno
export CLOUDINARY_CLOUD_NAME="dfkhuibwf"
export CLOUDINARY_API_KEY="857993365988948"
export CLOUDINARY_API_SECRET="ccEnjqy6Kj4UYri9U2fsl4gdDfI"

echo "✅ Variables configuradas:"
echo "CLOUDINARY_CLOUD_NAME: $CLOUDINARY_CLOUD_NAME"
echo "CLOUDINARY_API_KEY: $CLOUDINARY_API_KEY"
echo "CLOUDINARY_API_SECRET: [OCULTO]"

echo ""
echo "🚀 Iniciando servidor con Cloudinary configurado..."
python manage.py runserver
