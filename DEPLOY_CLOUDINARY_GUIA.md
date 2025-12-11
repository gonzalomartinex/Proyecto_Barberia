# 🚀 GUÍA DE DEPLOY - VARIABLES DE ENTORNO CLOUDINARY

## 📋 Variables de Entorno REQUERIDAS en Render

Para que Cloudinary y las imágenes funcionen correctamente, configura estas variables en tu Dashboard de Render:

### 🔐 **Variables Obligatorias**

```bash
# === CLOUDINARY (REQUERIDAS) ===
CLOUDINARY_CLOUD_NAME=dfkhuibwf
CLOUDINARY_API_KEY=[TU_API_KEY_DE_CLOUDINARY]
CLOUDINARY_API_SECRET=[TU_API_SECRET_DE_CLOUDINARY]

# === DJANGO BÁSICAS ===
DEBUG=False
DJANGO_SECRET_KEY=[TU_SECRET_KEY_SEGURA_ALEATORIA]
ALLOWED_HOSTS=proyecto-barberia-saw3.onrender.com,[otros_dominios_si_los_tienes]

# === BASE DE DATOS ===
# DATABASE_URL se configura automáticamente en Render si tienes PostgreSQL
```

## 🔍 **Cómo obtener las credenciales de Cloudinary**

1. Ve a: https://console.cloudinary.com/console
2. En el Dashboard principal verás un recuadro con:
   ```
   Cloud name: dfkhuibwf ✅ (ya lo tienes)
   API Key: 123456789012345 ← COPIA ESTE NÚMERO
   API Secret: abcdef1234567890 ← COPIA ESTA CADENA
   ```

## ⚙️ **Configuración en Render**

1. Ve a tu servicio en Render
2. Navega a la pestaña **"Environment"**
3. Haz clic en **"Add Environment Variable"**
4. Agrega cada variable:
   - **Key**: `CLOUDINARY_API_KEY`
   - **Value**: `tu_numero_api_key`
   - Repite para todas las variables

## 🎯 **¿Qué se solucionó?**

### ✅ **Problema de Archivos Excel (Error 500)**
- Vista `listar_archivos_excel` robusta con manejo de errores
- Archivos almacenados en BD (no archivos efímeros)
- Manejo individual de errores para cada archivo

### ✅ **Card "Administrar Cursos" en Admin Panel**
- URL corregida: `administracion-cursos` → `cursos-list`
- Card ahora funciona y lleva a la página de cursos

### ✅ **Sistema de Imágenes Ultra-Robusto**
- Todas las imágenes (JPEG, PNG, WebP) funcionan perfectamente
- Sistema de diagnóstico implementado
- Conversión automática y redimensionamiento inteligente

## 🔧 **Verificaciones Post-Deploy**

Después del deploy, verifica que funcionen:

1. **Página de cursos**: https://tu-app.onrender.com/cursos/
2. **Admin panel**: https://tu-app.onrender.com/admin-panel/
3. **Archivos Excel**: https://tu-app.onrender.com/administracion/turnos/archivos/
4. **Subida de imágenes** en cursos desde el admin de Django

## 🎉 **Resultado Esperado**

- ✅ Sistema de imágenes 100% funcional con Cloudinary
- ✅ Archivos Excel sin error 500
- ✅ Card "Administrar Cursos" funcional
- ✅ Modo oscuro completo y responsivo
- ✅ Todo optimizado para producción

## 🆘 **Si algo no funciona**

1. Verifica que todas las variables de entorno estén configuradas
2. Revisa los logs de Render en la pestaña "Logs"
3. Las credenciales de Cloudinary deben ser exactas (sin espacios)

---
**Deploy realizado el**: 11 de diciembre de 2025
**Commit**: `Fix: Vista robusta archivos Excel + Card administrar cursos + Mejoras sistema imágenes`
