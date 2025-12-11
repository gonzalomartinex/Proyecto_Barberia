#!/bin/bash
# Script para demostrar el uso de los comandos mejorados de backup con Cloudinary

echo "🔧 COMANDOS MEJORADOS DE BACKUP CON CLOUDINARY"
echo "=============================================="
echo ""

echo "📦 1. CREAR BACKUP COMPATIBLE CON CLOUDINARY:"
echo "python manage.py crear_backup_cloudinary --format=full --include-cloudinary"
echo ""
echo "   Opciones disponibles:"
echo "   --format: json, sqlite, full"
echo "   --cloudinary-backup-mode: urls, download, both"
echo "   --include-cloudinary: incluir metadatos e imágenes de Cloudinary"
echo ""

echo "🔄 2. MIGRAR BACKUP ANTIGUO (BINARIO) A CLOUDINARY:"
echo "python manage.py migrar_backup <archivo_backup> --dry-run"
echo ""
echo "   Ejemplo:"
echo "   python manage.py migrar_backup media/backups/backup_20241210.db --dry-run"
echo "   python manage.py migrar_backup media/backups/backup_20241210.zip"
echo ""

echo "🔍 3. ANALIZAR BACKUP ANTES DE MIGRAR:"
echo "python manage.py migrar_backup <archivo> --dry-run"
echo ""

echo "💡 VENTAJAS DE LOS NUEVOS COMANDOS:"
echo "=================================="
echo "✅ Compatibles con Cloudinary (URLs en vez de datos binarios)"
echo "✅ Pueden migrar backups antiguos automáticamente"
echo "✅ Opción de descargar imágenes de Cloudinary como respaldo"
echo "✅ Metadatos detallados sobre las imágenes"
echo "✅ Análisis previo con --dry-run antes de migrar"
echo ""

echo "⚠️  IMPORTANTE:"
echo "==============="
echo "• Los backups antiguos con imágenes binarias necesitan migración"
echo "• La migración sube las imágenes binarias a Cloudinary automáticamente"
echo "• Se recomienda hacer backup de Cloudinary periódicamente"
echo "• Usar --dry-run primero para ver qué se haría"
echo ""

# Verificar si hay backups antiguos
if [ -d "media/backups" ]; then
    echo "📁 BACKUPS EXISTENTES:"
    echo "====================="
    find media/backups -name "*.db" -o -name "*.zip" -o -name "*.json" | head -5
    echo ""
fi

echo "🚀 Para empezar, ejecuta:"
echo "python manage.py crear_backup_cloudinary --help"
