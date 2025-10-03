# Configuración de directorios de imágenes
# Este archivo define qué directorios contienen imágenes por defecto (servidas por WhiteNoise)
# y cuáles son para uploads de usuarios (manejados por Cloudinary)

# Directorios de imágenes por defecto (incluidos en el código fuente)
DEFAULT_IMAGE_DIRS = [
    'Default',      # Imágenes placeholder (noimage.png, perfil_default.png)
    'logo',         # Logos de la barbería
    'carousel',     # Imágenes del carousel principal
]

# Directorios para uploads de usuarios (van a Cloudinary en producción)
USER_UPLOAD_DIRS = [
    'usuarios',     # Fotos de perfil de usuarios
    'barberos',     # Fotos de barberos
    'servicios',    # Imágenes de servicios
    'productos',    # Imágenes de productos
    'cursos',       # Imágenes de cursos
    'archivos_turnos',  # Archivos relacionados con turnos
]

# Función para determinar si una imagen es por defecto o upload de usuario
def is_default_image(image_path):
    """
    Determina si una imagen es por defecto (servida por WhiteNoise)
    o un upload de usuario (manejado por Cloudinary)
    """
    path_parts = image_path.split('/')
    if len(path_parts) > 0:
        first_dir = path_parts[0]
        return first_dir in DEFAULT_IMAGE_DIRS
    return False
