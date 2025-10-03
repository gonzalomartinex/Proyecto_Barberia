# Configuración Final de Imágenes

## Resumen
El sistema de gestión de imágenes está configurado para funcionar correctamente tanto en desarrollo como en producción (Render.com).

## Separación de Imágenes

### Imágenes Estáticas (Archivos por defecto)
**Ubicación**: `/static/`
**Servidas por**: WhiteNoise
**Incluyen**:
- `/static/logo/logo.png` - Logo principal
- `/static/logo/logoblanco.png` - Logo blanco para navbar
- `/static/Default/noimage.png` - Imagen placeholder para productos/barberos sin imagen
- `/static/Default/perfil_default.png` - Imagen por defecto para perfiles de usuario
- `/static/carousel/` - Imágenes por defecto del carrusel

**Uso en plantillas**:
```django
{% load static %}
<img src="{% static 'logo/logo.png' %}" alt="Logo">
```

### Imágenes Dinámicas (Subidas por usuarios)
**Ubicación**: Cloudinary (en producción) / `/media/` (en desarrollo)
**Servidas por**: Cloudinary CDN / Django devserver
**Incluyen**:
- Fotos de barberos subidas por admin
- Imágenes de productos subidas por admin
- Imágenes de servicios subidas por admin
- Imágenes de cursos subidas por admin
- Fotos de perfil subidas por usuarios
- Archivos de turnos (Excel)

**Uso en plantillas**:
```django
<img src="{{ objeto.imagen.url }}" alt="Imagen dinámica">
```

## Configuración en settings.py

### Archivos Estáticos
```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # Archivos estáticos de la aplicación
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Archivos Media (Cloudinary)
```python
if 'CLOUDINARY_URL' in os.environ:
    # Producción - usar Cloudinary
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
        'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
        'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
    }
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    MEDIA_URL = f"https://res.cloudinary.com/{os.getenv('CLOUDINARY_CLOUD_NAME')}/image/upload/"
else:
    # Desarrollo - usar archivos locales
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
```

## Variables de Entorno Requeridas en Render

```
CLOUDINARY_CLOUD_NAME=tu_cloud_name
CLOUDINARY_API_KEY=tu_api_key
CLOUDINARY_API_SECRET=tu_api_secret
CLOUDINARY_UPLOAD_PRESET=django-media
```

## Comandos de Deploy

El script `build.sh` ejecuta automáticamente:
1. `collectstatic` - Recopila archivos estáticos
2. `copy_media_to_static` - Copia algunos media a static (si es necesario)
3. `diagnosticar_cloudinary` - Verifica configuración de Cloudinary

## Funcionamiento

### En Desarrollo
- Archivos estáticos: servidos por Django desde `/static/`
- Archivos media: servidos por Django desde `/media/`

### En Producción (Render)
- Archivos estáticos: servidos por WhiteNoise desde `/staticfiles/`
- Archivos media: servidos por Cloudinary CDN
- Imágenes por defecto siempre disponibles vía WhiteNoise
- Imágenes subidas persisten en Cloudinary

## Beneficios de esta Configuración

1. **Rendimiento**: Las imágenes estáticas se cargan rápidamente desde WhiteNoise
2. **Persistencia**: Las imágenes subidas se almacenan permanentemente en Cloudinary
3. **Escalabilidad**: Cloudinary maneja el redimensionamiento y optimización automática
4. **Confiabilidad**: Las imágenes por defecto nunca fallan porque están en el código fuente
5. **SEO**: URLs de imágenes consistentes y optimizadas

## Mantenimiento

- Las imágenes por defecto se actualizan modificando archivos en `/static/` y haciendo deploy
- Las imágenes subidas se gestionan automáticamente por Cloudinary
- Los logs de Cloudinary están disponibles en el dashboard de Cloudinary
- El comando `diagnosticar_cloudinary` ayuda a detectar problemas de configuración
