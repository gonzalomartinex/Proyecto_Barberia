import os
import random
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
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

@user_passes_test(lambda u: u.is_superuser)
def editar_carrusel(request):
    """Vista para editar las imágenes del carrusel"""
    if request.method == 'POST':
        # Procesar la subida de nuevas imágenes
        uploaded_files = request.FILES.getlist('nuevas_imagenes')
        carousel_dir = Path(settings.MEDIA_ROOT) / 'carousel'
        carousel_dir.mkdir(exist_ok=True)
        
        for uploaded_file in uploaded_files:
            if uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                file_path = carousel_dir / uploaded_file.name
                with open(file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
        
        if uploaded_files:
            messages.success(request, f'Se subieron {len(uploaded_files)} imágenes correctamente.')
        
        return redirect('editar-carrusel')
    
    # Obtener imágenes actuales del carrusel
    carousel_dir = Path(settings.MEDIA_ROOT) / 'carousel'
    carousel_images = []
    if carousel_dir.exists():
        for fname in os.listdir(carousel_dir):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                carousel_images.append(f'/media/carousel/{fname}')
    
    return render(request, 'editar_carrusel.html', {'carousel_images': carousel_images})
