#!/bin/bash

# Deploy Cloudinary Fix - Barbería Project
echo "🚀 Desplegando proyecto con configuración Cloudinary actualizada..."
echo "================================================"

# Verificar que estamos en la rama correcta
echo "📋 Estado del repositorio:"
git status

echo "📁 Archivos modificados:"
git diff --name-only

# Confirmar cambios
echo ""
read -p "¿Deseas confirmar los cambios y hacer deploy? (y/N): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "❌ Deploy cancelado"
    exit 1
fi

# Agregar y confirmar cambios
echo "💾 Confirmando cambios..."
git add .
git commit -m "Fix: Actualizar credenciales Cloudinary para producción

- Configurar CLOUDINARY_CLOUD_NAME: dfkhulbwf
- Configurar CLOUDINARY_API_KEY: 857993365988948
- Configurar CLOUDINARY_API_SECRET para producción
- Resolver problema de imágenes no visibles en Render"

# Push a la rama principal
echo "📤 Enviando cambios al repositorio..."
git push origin main

echo ""
echo "✅ Deploy completado!"
echo "📋 Próximos pasos:"
echo "   1. Ve a tu dashboard de Render"
echo "   2. El deploy debería iniciarse automáticamente"
echo "   3. Revisa los logs de build y deploy"
echo "   4. Prueba la subida de imágenes en producción"
echo "   5. Verifica que las imágenes se muestren correctamente"
echo ""
echo "🔗 Enlaces útiles:"
echo "   - Dashboard Render: https://dashboard.render.com"
echo "   - Dashboard Cloudinary: https://cloudinary.com/console"
echo "   - Logs de tu aplicación en Render"
echo ""
