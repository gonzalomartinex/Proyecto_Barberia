# 🚀 Guía de Despliegue - Barbería Cortes Con Historia

## 📋 Requisitos del Servidor

### Software necesario:
- Python 3.8+
- MySQL 5.7+ o MariaDB
- pip (gestor de paquetes Python)
- Git (para clonar el repositorio)

### Paquetes del sistema (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv mysql-server git
sudo apt install libmysqlclient-dev python3-dev
```

## 🗄️ Configuración de Base de Datos

### 1. Configurar MySQL:
```sql
-- Conectar como root
sudo mysql -u root -p

-- Crear base de datos y usuario
CREATE DATABASE barberia_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'barberia_user'@'localhost' IDENTIFIED BY 'tu_password_seguro';
GRANT ALL PRIVILEGES ON barberia_db.* TO 'barberia_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 📁 Despliegue del Proyecto

### 1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/proyecto-barberia.git
cd proyecto-barberia
```

### 2. Crear entorno virtual:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno:
```bash
cp .env.ejemplo .env
nano .env  # Editar con tu configuración
```

### 5. Ejecutar script de configuración:
```bash
./setup_servidor.sh
```

## 🔧 Configuración para Producción

### 1. Nginx (Servidor web):
```nginx
server {
    listen 80;
    server_name tu-dominio.com;
    
    location /static/ {
        alias /ruta/a/tu/proyecto/staticfiles/;
    }
    
    location /media/ {
        alias /ruta/a/tu/proyecto/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Gunicorn (Servidor de aplicaciones):
```bash
# Instalar gunicorn
pip install gunicorn

# Ejecutar servidor
gunicorn BarberiaApp.wsgi:application --bind 127.0.0.1:8000
```

### 3. Systemd (Servicio del sistema):
Crear archivo `/etc/systemd/system/barberia.service`:
```ini
[Unit]
Description=Barberia Django App
After=network.target

[Service]
User=tu-usuario
Group=www-data
WorkingDirectory=/ruta/a/tu/proyecto
Environment="PATH=/ruta/a/tu/proyecto/venv/bin"
ExecStart=/ruta/a/tu/proyecto/venv/bin/gunicorn --workers 3 --bind unix:/ruta/a/tu/proyecto/barberia.sock BarberiaApp.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🔒 Seguridad

### Configuraciones importantes:
1. **Cambiar SECRET_KEY** en `.env`
2. **Cambiar contraseña del admin**
3. **Configurar ALLOWED_HOSTS** correctamente
4. **Usar HTTPS** en producción
5. **Configurar firewall** del servidor

## 📊 Datos Iniciales

### El sistema incluye:
- ✅ **Migraciones**: Recrean toda la estructura de BD
- ✅ **Script de setup**: Configura usuario admin
- ✅ **Fixtures**: Datos iniciales (si los hay)
- ✅ **Directorios media**: Para archivos subidos

### Usuario administrador inicial:
- **Email**: admin@cortesconhistoria.com
- **Contraseña**: admin123
- ⚠️ **CAMBIAR** en producción

## 🛠️ Comandos Útiles

```bash
# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recopilar archivos estáticos
python manage.py collectstatic

# Cargar datos iniciales
python manage.py loaddata fixtures/*.json

# Hacer backup de la BD
python manage.py dumpdata > backup.json

# Reiniciar servicio
sudo systemctl restart barberia
```

## 📞 Soporte

Si encuentras problemas durante el despliegue:
1. Revisar logs: `sudo journalctl -u barberia`
2. Verificar configuración de BD
3. Comprobar permisos de archivos
4. Revisar configuración de Nginx/Apache

---

💡 **Nota**: Esta guía asume un servidor Linux. Para otros sistemas operativos, ajustar los comandos según corresponda.
