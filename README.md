# Proyecto Barbería

## Guía completa para levantar el proyecto desde cero

### 1. Clonar el repositorio

Abre una terminal y ejecuta:

```bash
git clone https://github.com/gonzalomartinex/Proyecto_Barberia.git
cd Proyecto_Barberia
```

### 2. Instalar Python 3 y dependencias del sistema

Asegúrate de tener Python 3 instalado. Si usas Linux (Ubuntu/Debian), instala también los paquetes necesarios para entornos virtuales y MySQL:

```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv libmysqlclient-dev
```

> **Nota:** Si al crear el entorno virtual ves un error como `ensurepip is not available`, instala el paquete `python3-venv` como se muestra arriba.

### 3. Crear y activar un entorno virtual (recomendado)

```bash
python3 -m venv venv
source venv/bin/activate
```

- Si usas Windows, activa el entorno con:
  ```cmd
  venv\Scripts\activate
  ```

### 4. Instalar las dependencias del proyecto

Con el entorno virtual activado:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configurar la base de datos y variables de entorno

1. Crea una base de datos MySQL vacía (puedes usar phpMyAdmin, DBeaver o consola):
   ```sql
   CREATE DATABASE nombre_base CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
2. Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido (ajusta los valores):
   ```env
   DB_NAME=nombre_base
   DB_USER=usuario
   DB_PASSWORD=contraseña
   DB_HOST=localhost
   DB_PORT=3306
   SECRET_KEY=tu_clave_secreta_django
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost
   ```
3. Si tienes archivos de medios o estáticos personalizados, revisa las carpetas `media/` y `staticfiles/`.

### 6. Aplicar migraciones de la base de datos

```bash
python3 manage.py migrate
```

### 7. Crear un superusuario para el panel de administración (opcional pero recomendado)

```bash
python3 manage.py createsuperuser
```

Sigue las instrucciones para definir usuario, email y contraseña.

### 8. Levantar el servidor de desarrollo

```bash
python3 manage.py runserver
```

- Si todo está bien, verás un mensaje como:
  > Starting development server at http://127.0.0.1:8000/

### 9. Acceder a la aplicación

Abre tu navegador y entra a:
- http://127.0.0.1:8000/  (sitio principal)
- http://127.0.0.1:8000/admin  (panel de administración)

---

## Problemas frecuentes y soluciones

- **Error `ensurepip is not available` al crear el entorno virtual:**
  - Solución: Ejecuta `sudo apt-get install python3-venv` y vuelve a intentarlo.
- **Error de conexión a MySQL:**
  - Verifica usuario, contraseña, nombre de base y que el servicio MySQL esté corriendo.
- **Faltan variables en `.env` o configuración:**
  - Asegúrate de que el archivo `.env` esté bien escrito y en la raíz del proyecto.

---

**Requisitos mínimos:**
- Python 3.8 o superior
- MySQL 5.7 o superior
- pip

**Contacto:**
Si tienes dudas, contacta a Gonzalo o abre un issue en el repositorio.
