#!/bin/bash
# Script de inicialización para servidor de producción
# Ejecutar después de configurar la base de datos

echo "🚀 CONFIGURANDO BARBERÍA - CORTES CON HISTORIA"
echo "=============================================="

# Aplicar migraciones
echo "📊 Aplicando migraciones de base de datos..."
python manage.py migrate

# Crear superusuario si no existe
echo "👤 Configurando usuario administrador..."
python manage.py shell -c "
from usuarios.models import Usuario
if not Usuario.objects.filter(is_superuser=True).exists():
    Usuario.objects.create_superuser(
        email='admin@cortesconhistoria.com',
        nombre='Administrador',
        apellido='Sistema',
        password='admin123',
        telefono='+54 9 351 123-4567'
    )
    print('✅ Superusuario creado: admin@cortesconhistoria.com / admin123')
else:
    print('ℹ️  Ya existe un superusuario en el sistema')
"

# Cargar datos iniciales si existen
if [ -d "fixtures" ]; then
    echo "📁 Cargando datos iniciales..."
    for fixture in fixtures/*.json; do
        if [ -f "$fixture" ]; then
            echo "   Cargando: $fixture"
            python manage.py loaddata "$fixture"
        fi
    done
fi

# Collectstatic para archivos estáticos
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Crear directorios necesarios
echo "📂 Creando directorios de media..."
mkdir -p media/barberos
mkdir -p media/carousel
mkdir -p media/cursos
mkdir -p media/productos
mkdir -p media/servicios
mkdir -p media/usuarios
mkdir -p media/archivos_turnos
mkdir -p media/Default

# Copiar imagen por defecto si no existe
if [ ! -f "media/Default/noimage.png" ]; then
    echo "🖼️  Configurando imagen por defecto..."
    # Aquí podrías copiar una imagen por defecto
    # cp static/images/default-user.png media/Default/noimage.png
fi

echo ""
echo "✅ CONFIGURACIÓN COMPLETADA"
echo "=========================="
echo "🌐 El sistema está listo para funcionar"
echo "👤 Usuario admin: admin@cortesconhistoria.com"
echo "🔑 Contraseña: admin123"
echo ""
echo "⚠️  IMPORTANTE: Cambiar la contraseña del admin en producción"
echo "⚠️  IMPORTANTE: Configurar variables de entorno (.env)"
