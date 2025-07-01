import os
import random
from django.conf import settings
from django.shortcuts import render
from pathlib import Path

def index(request):
    # Carpeta raíz de imágenes
    image_dirs = [
        Path(settings.MEDIA_ROOT) / 'barberos/fotos',
        Path(settings.MEDIA_ROOT) / 'barberos/trabajos',
        Path(settings.MEDIA_ROOT) / 'productos/imagenes',
        Path(settings.MEDIA_ROOT) / 'servicios/imagenes',
    ]
    all_images = []
    for dir_path in image_dirs:
        if dir_path.exists():
            for fname in os.listdir(dir_path):
                if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                    rel_path = dir_path.relative_to(settings.MEDIA_ROOT) / fname
                    all_images.append(str(rel_path))
    random_images = random.sample(all_images, min(5, len(all_images))) if all_images else []
    random_images = [f'/media/{img}' for img in random_images]
    return render(request, 'index.html', {'carousel_images': random_images})
