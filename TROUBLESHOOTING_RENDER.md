# Troubleshooting: Repositorio no aparece en Render

## Problema
El repositorio `Proyecto_Barberia` no aparece en la lista de repositorios disponibles en Render.com al intentar crear un nuevo Web Service.

## Posibles Causas y Soluciones

### 1. **Verificar Visibilidad del Repositorio**

**Paso 1**: Verificar si el repositorio es público
- Ve a: https://github.com/gonzalomartinex/Proyecto_Barberia
- Si ves un mensaje de "404" o "Repository not found", el repositorio puede ser privado
- **Solución**: Hacer el repositorio público

**Para hacer público el repositorio:**
1. Ve a tu repositorio en GitHub
2. Clic en "Settings" (configuración)
3. Scroll hasta abajo hasta "Danger Zone"
4. Clic en "Change repository visibility"
5. Selecciona "Make public"

### 2. **Reconectar GitHub con Render**

**Paso 1**: Desconectar y reconectar GitHub
1. En Render Dashboard, ve a "Account Settings"
2. En la sección "Connected Accounts", desconecta GitHub
3. Vuelve a conectar GitHub con permisos completos

**Paso 2**: Autorizar Render en GitHub
1. Ve a GitHub.com → Settings → Applications → Authorized OAuth Apps
2. Busca "Render" y asegúrate de que tenga permisos para acceder a repositories
3. Si no está o tiene permisos limitados, revoca y vuelve a autorizar

### 3. **Refresh Manual en Render**

1. En la página de "Create a new Web Service"
2. Busca un botón de "Refresh" o "Sync repositories"
3. Espera unos minutos y vuelve a cargar la página

### 4. **Usar URL Directa del Repositorio**

Si el repositorio sigue sin aparecer, puedes intentar:
1. En lugar de seleccionar de la lista, busca una opción "Connect a repository"
2. Introduce la URL directa: `https://github.com/gonzalomartinex/Proyecto_Barberia`

### 5. **Verificar Configuración del Repositorio**

Asegúrate de que el repositorio tenga:
- [x] `render.yaml` en la raíz
- [x] `build.sh` en la raíz  
- [x] `requirements.txt` actualizado
- [x] Configuración correcta de Django en `settings.py`

### 6. **Método Alternativo: Fork del Repositorio**

Si nada funciona:
1. Haz un fork del repositorio en tu cuenta personal
2. Asegúrate de que el fork sea público
3. Usa el fork para el deployment en Render

## Comandos de Verificación

```bash
# Verificar configuración del repositorio
git remote -v
git status
git log --oneline -5

# Verificar archivos necesarios
ls -la render.yaml build.sh requirements.txt
```

## Siguiente Paso: Deployment Manual

Si el repositorio sigue sin aparecer, podemos:
1. Crear un nuevo repositorio público
2. Copiar todo el código
3. Hacer el deployment desde el nuevo repositorio

## Información del Proyecto

- **Repositorio**: `gonzalomartinex/Proyecto_Barberia`
- **Rama principal**: `main`
- **Archivos de configuración**: ✅ Completos
- **Estado**: Listo para deployment

## 🔒 Alternativa Segura: Repository Temporal

Si no quieres hacer público tu repositorio principal:

### Opción A: Repository Temporal
1. Crea un nuevo repositorio público temporal: `Proyecto_Barberia_Deploy`
2. Clona y empuja todo el código:
```bash
# Crear nuevo repositorio en GitHub (público)
git clone https://github.com/gonzalomartinex/Proyecto_Barberia.git temp-deploy
cd temp-deploy
git remote set-url origin https://github.com/gonzalomartinex/Proyecto_Barberia_Deploy.git
git push -u origin main
```
3. Usa este repositorio para Render
4. Una vez funcionando, elimina el repositorio temporal
5. Reconfigura Render para usar el repositorio original (ya conectado)

### Opción B: Hacer Público Temporalmente (Recomendado)
1. **Público** → Conectar Render → **Primer Deploy Exitoso** → **Privado**
2. Total tiempo público: ~30-60 minutos
3. Render mantiene conexión permanente

## 🎯 Recomendación

**Opción B es más simple y segura** porque:
- Tiempo público mínimo
- Una sola configuración
- Sin repositorios duplicados
- Render mantiene acceso OAuth permanente

# 🔧 Errores Comunes en Deployment de Render

Basado en la documentación oficial de Render: https://render.com/docs/troubleshooting-deploys

## 🚨 ModuleNotFoundError: Errores más frecuentes

### **Causa Principal**
- Dependencias faltantes en `requirements.txt`
- Versiones incompatibles entre desarrollo local y Render

### **Errores Resueltos en este Proyecto:**
1. ✅ `python-decouple` (eliminado - no necesario)
2. ✅ `django-environ` (agregado)
3. ✅ `djangorestframework-simplejwt` (agregado)  
4. ✅ `pkg_resources/setuptools` (agregado)
5. ✅ `pytz` (agregado)
6. ✅ `wheel` (agregado para build tools)

### **Requirements.txt Final Optimizado:**
```
# Core Django
Django==5.2.3
djangorestframework==3.16.0
djangorestframework-simplejwt==5.3.0

# Image processing
Pillow==11.2.1

# Production server
gunicorn==23.0.0

# Database
psycopg2-binary==2.9.10
dj-database-url==2.3.0

# Static files and configuration
whitenoise==6.8.2
django-environ==0.11.2

# Timezone support
pytz==2024.1

# Build tools
setuptools==69.5.1
wheel==0.42.0
```

## 📋 Build Script Optimizado

```bash
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
```

## 🎯 Próximos Pasos Probables

1. **Build exitoso de dependencias** ✅
2. **Collectstatic** - Recolección de archivos estáticos
3. **Migrate** - Migraciones de base de datos (posible error de BD)
4. **Start** - Inicio de aplicación con Gunicorn

### **Posibles Próximos Errores:**

#### **Error de Base de Datos:**
- Necesitarás crear PostgreSQL database en Render
- Actualizar variable `DATABASE_URL`

#### **Error de Archivos Estáticos:**
- Verificar configuración de WhiteNoise
- Confirmar `STATIC_ROOT` en settings.py

#### **Error de Hosts Permitidos:**
- Actualizar `ALLOWED_HOSTS` con el dominio de Render

## ✅ Mejores Prácticas Aplicadas

- **Versiones específicas** en requirements.txt
- **Build tools actualizados** (setuptools, wheel)
- **Dependencias organizadas** por categoría
- **Script de build robusto** con manejo de errores
