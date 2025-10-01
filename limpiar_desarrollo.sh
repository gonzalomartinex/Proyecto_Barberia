#!/bin/bash
# Script para limpiar archivos de desarrollo y testing

echo "=== LIMPIEZA DE ARCHIVOS DE DESARROLLO ==="

# Lista de archivos a mantener para referencia
echo "Archivos que se mantendrán para referencia:"
echo "- crear_escenario_visual.py (para testing visual)"
echo "- validacion_restriccion_final.py (para validación automática)"

# Crear directorio de backup para archivos de desarrollo
mkdir -p backup_desarrollo

# Mover archivos de desarrollo al backup
echo ""
echo "Moviendo archivos de desarrollo al directorio backup_desarrollo/:"

# Debug files
for file in debug_*.py; do
    if [ -f "$file" ]; then
        echo "- $file"
        mv "$file" backup_desarrollo/
    fi
done

# Demo files (excepto el escenario visual)
for file in demo_*.py; do
    if [ -f "$file" ] && [ "$file" != "crear_escenario_visual.py" ]; then
        echo "- $file"
        mv "$file" backup_desarrollo/
    fi
done

# Test files obsoletos
obsolete_tests=(
    "test_busqueda_corregida.py"
    "test_busqueda_usuarios_actualizada.py" 
    "test_busqueda_usuarios.py"
    "test_formateo_final.py"
    "test_nuevo_nombre.py"
    "test_registro_formateo.py"
    "test_restriccion_semanal.py"
    "validacion_busqueda_final.py"
    "validacion_final_sistema.py"
)

for file in "${obsolete_tests[@]}"; do
    if [ -f "$file" ]; then
        echo "- $file"
        mv "$file" backup_desarrollo/
    fi
done

echo ""
echo "=== ARCHIVOS MANTENIDOS ==="
echo "Los siguientes archivos se mantienen en el directorio principal:"
ls -la *.py | grep -E "(crear_escenario_visual|validacion_restriccion_final|crear_notificaciones_ejemplo|crear_turnos_usuario_ejemplo|crear_turno_test|demo_sistema_cancelacion|test_archivado|test_cancelacion_tardia|test_comando|completar_historial_turnos|limpiar_notificaciones|verificar_excel)" || echo "- Archivos principales de gestión"

echo ""
echo "=== RESUMEN ==="
echo "✅ Archivos de desarrollo movidos a backup_desarrollo/"
echo "✅ Archivos de validación y escenarios visuales mantenidos"
echo "✅ Sistema listo para producción"
echo ""
echo "Para restaurar archivos de desarrollo: mv backup_desarrollo/* ."
