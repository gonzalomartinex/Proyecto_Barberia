# Proyecto Barbería

## Pasos para levantar el proyecto en otra PC

1. **Clona el repositorio:**

```bash
git clone https://github.com/gonzalomartinex/Proyecto_Barberia.git
cd Proyecto_Barberia
```

2. **Crea y activa un entorno virtual (opcional pero recomendado):**

```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Instala las dependencias:**

```bash
pip install -r requirements.txt
```

4. **Configura la base de datos:**

- Crea una base de datos MySQL y configura las credenciales en el archivo `.env` o en la configuración de Django (`settings.py`).
- Ejemplo de variables en `.env`:

```
DB_NAME=nombre_base
DB_USER=usuario
DB_PASSWORD=contraseña
DB_HOST=localhost
DB_PORT=3306
```

5. **Realiza las migraciones:**

```bash
python3 manage.py migrate
```

6. **Crea un superusuario (opcional, para acceder al admin):**

```bash
python3 manage.py createsuperuser
```

7. **Levanta el servidor de desarrollo:**

```bash
python3 manage.py runserver
```

8. **Accede a la app:**

Abre tu navegador en http://127.0.0.1:8000/

---

**Notas:**
- Asegúrate de tener MySQL y Python 3 instalados.
- Si usas Windows, los comandos de entorno virtual pueden variar.
- Si tienes archivos estáticos o de medios personalizados, revisa las carpetas `media/` y `staticfiles/`.
