# 🚀 Deploy en Render.com - Proyecto Barbería

## Preparación Completada ✅

Los archivos de configuración ya están listos:
- `render.yaml` - Configuración de servicios
- `build.sh` - Script de construcción
- `requirements.txt` - Dependencias actualizadas
- `settings.py` - Configurado para producción

## 📋 Pasos para Deploy

### **1. Preparar el Repositorio**

```bash
# Agregar archivos de configuración al repositorio
git add render.yaml build.sh requirements.txt BarberiaApp/settings.py .env.ejemplo
git commit -m "Configuración para deploy en Render"
git push origin main
```

### **2. Crear Cuenta en Render.com**

1. Ve a [render.com](https://render.com)
2. Regístrate con tu cuenta de GitHub
3. Conecta tu repositorio GitHub

### **3. Crear el Servicio Web**

1. **Dashboard de Render** → "New" → "Web Service"
2. **Connect Repository**: Selecciona `gonzalomartinex/Proyecto_Barberia`
3. **Configuración básica**:
   - **Name**: `barberia-app`
   - **Environment**: `Python 3`
   - **Region**: `Oregon (US West)` o el más cercano
   - **Branch**: `main`

4. **Build & Deploy**:
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn BarberiaApp.wsgi:application`

### **4. Crear Base de Datos PostgreSQL**

1. **Dashboard** → "New" → "PostgreSQL"
2. **Configuración**:
   - **Name**: `barberia-db`
   - **Database Name**: `barberia`
   - **User**: `barberia_user`
   - **Region**: Same as web service
   - **Plan**: `Free`

### **5. Configurar Variables de Entorno**

En tu Web Service, ve a "Environment" y agrega:

```
DJANGO_SECRET_KEY=<será generado automáticamente>
DEBUG=False
ALLOWED_HOSTS=.render.com
DATABASE_URL=<conectar con la base de datos creada>
DISABLE_COLLECTSTATIC=1
```

### **6. Conectar Base de Datos**

1. En "Environment Variables"
2. Busca `DATABASE_URL`
3. Selecciona "Add from Database"
4. Elige `barberia-db` → `Connection String`

### **7. Deploy**

1. Haz clic en "Create Web Service"
2. Render automáticamente:
   - Clonará el repositorio
   - Instalará dependencias
   - Ejecutará migraciones
   - Recopilará archivos estáticos
   - Iniciará la aplicación

### **8. Verificación Post-Deploy**

Una vez que el deploy termine:

1. **Accede a tu aplicación**: `https://barberia-app-xxxx.onrender.com`
2. **Crear superusuario** (desde el Shell en Render):
   ```bash
   python manage.py createsuperuser
   ```

### **9. Configuraciones Adicionales**

#### Cargar Datos Iniciales (Opcional)
```bash
python manage.py loaddata fixtures/barberos_inicial.json
python manage.py loaddata fixtures/servicios_inicial.json
python manage.py loaddata fixtures/productos_inicial.json
```

#### Configurar Dominio Personalizado
1. **Settings** → "Custom Domains"
2. Agregar tu dominio
3. Configurar DNS según las instrucciones

## 🔧 Troubleshooting

### Error de Migraciones
```bash
python manage.py migrate --run-syncdb
```

### Error de Archivos Estáticos
```bash
python manage.py collectstatic --clear --no-input
```

### Error de Base de Datos
- Verificar que `DATABASE_URL` esté correctamente configurada
- Confirmar que la base de datos PostgreSQL esté en la misma región

## 🌐 URLs Finales

- **Aplicación**: `https://barberia-app.onrender.com`
- **Admin**: `https://barberia-app.onrender.com/admin/`
- **API**: `https://barberia-app.onrender.com/api/`

## 📝 Notas Importantes

- **Plan Gratuito**: La aplicación puede "dormir" después de 15 minutos de inactividad
- **Tiempo de Inicio**: La primera carga puede tomar 30-60 segundos
- **Base de Datos**: PostgreSQL gratis tiene límite de 1GB
- **Rendimiento**: Para producción real, considera el plan pago

## ⚡ Actualizaciones

Para actualizar la aplicación:
1. Haz push a `main` en GitHub
2. Render automáticamente hará redeploy
3. O manualmente desde "Manual Deploy"

¡Tu barbería estará online en minutos! 🎉
