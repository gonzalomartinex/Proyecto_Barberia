#!/bin/bash
# Script para ejecutar el servidor de desarrollo con el entorno virtual activado

echo "🚀 INICIANDO SERVIDOR DE DESARROLLO - SISTEMA ADMINISTRACIÓN DE CURSOS"
echo "=" * 70

# Activar entorno virtual
echo "📦 Activando entorno virtual..."
source venv/bin/activate

# Verificar configuración
echo "🔍 Verificando configuración Django..."
python manage.py check

if [ $? -eq 0 ]; then
    echo "✅ Configuración verificada exitosamente"
    echo ""
    echo "🌐 INICIANDO SERVIDOR EN http://127.0.0.1:8000"
    echo ""
    echo "📋 ACCESOS PRINCIPALES:"
    echo "   • Panel Administración General: http://127.0.0.1:8000/admin-panel/"
    echo "   • Administración de Cursos: http://127.0.0.1:8000/cursos/administracion/"
    echo "   • Lista Pública de Cursos: http://127.0.0.1:8000/cursos/"
    echo "   • Crear Nuevo Curso: http://127.0.0.1:8000/cursos/crear/"
    echo "   • Exportar Cursos CSV: http://127.0.0.1:8000/cursos/exportar/"
    echo ""
    echo "🎯 Para detener el servidor: Ctrl+C"
    echo "=" * 70
    
    # Iniciar servidor
    python manage.py runserver
else
    echo "❌ Error en la configuración. Revisa los errores anteriores."
fi
