import os
import random
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db import models
from pathlib import Path

def index(request):
    """Vista principal - muestra las imágenes del carrusel"""
    from .models import CarouselImage
    
    # Obtener imágenes del carrusel ordenadas
    carousel_images = CarouselImage.objects.all()
    
    # Si no hay imágenes en el carrusel, usar imágenes por defecto
    if not carousel_images:
        # Carpeta raíz de imágenes por defecto
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
        carousel_data = [f'/media/{img}' for img in random_images]
    else:
        # Usar imágenes del carrusel
        carousel_data = [img.imagen.url for img in carousel_images]
    
    return render(request, 'index.html', {'carousel_images': carousel_data})

@user_passes_test(lambda u: u.is_superuser)
def editar_carrusel(request):
    """Vista para editar las imágenes del carrusel"""
    from .models import CarouselImage
    from .forms import CarouselImageForm
    from django.contrib import messages
    
    if request.method == 'POST':
        if 'add' in request.POST:
            # Agregar nueva imagen
            form = CarouselImageForm(request.POST, request.FILES)
            if form.is_valid():
                # Obtener el último orden y agregar 1
                ultimo_orden = CarouselImage.objects.aggregate(
                    max_orden=models.Max('orden')
                )['max_orden'] or 0
                
                carousel_image = form.save(commit=False)
                carousel_image.orden = ultimo_orden + 1
                carousel_image.save()
                
                messages.success(request, 'Imagen agregada correctamente.')
            else:
                messages.error(request, 'Error al agregar la imagen.')
                
        elif 'delete' in request.POST:
            # Eliminar imagen
            image_id = request.POST.get('delete')
            try:
                image = CarouselImage.objects.get(id=image_id)
                image.imagen.delete()  # Eliminar archivo físico
                image.delete()
                # Reordenar imágenes restantes
                for i, img in enumerate(CarouselImage.objects.all(), 1):
                    img.orden = i
                    img.save()
                messages.success(request, 'Imagen eliminada correctamente.')
            except CarouselImage.DoesNotExist:
                messages.error(request, 'La imagen no existe.')
                
        elif 'move_left' in request.POST:
            # Mover imagen a la izquierda
            image_id = request.POST.get('move_left')
            try:
                image = CarouselImage.objects.get(id=image_id)
                if image.orden > 1:
                    # Intercambiar con la imagen anterior
                    prev_image = CarouselImage.objects.get(orden=image.orden - 1)
                    image.orden, prev_image.orden = prev_image.orden, image.orden
                    image.save()
                    prev_image.save()
                    messages.success(request, 'Imagen movida correctamente.')
            except CarouselImage.DoesNotExist:
                messages.error(request, 'Error al mover la imagen.')
                
        elif 'move_right' in request.POST:
            # Mover imagen a la derecha
            image_id = request.POST.get('move_right')
            try:
                image = CarouselImage.objects.get(id=image_id)
                max_orden = CarouselImage.objects.aggregate(
                    max_orden=models.Max('orden')
                )['max_orden'] or 0
                
                if image.orden < max_orden:
                    # Intercambiar con la imagen siguiente
                    next_image = CarouselImage.objects.get(orden=image.orden + 1)
                    image.orden, next_image.orden = next_image.orden, image.orden
                    image.save()
                    next_image.save()
                    messages.success(request, 'Imagen movida correctamente.')
            except CarouselImage.DoesNotExist:
                messages.error(request, 'Error al mover la imagen.')
        
        return redirect('editar-carrusel')
    
    # GET request
    form = CarouselImageForm()
    images = CarouselImage.objects.all()
    
    return render(request, 'editar_carrusel.html', {
        'form': form,
        'images': images
    })

@user_passes_test(lambda u: u.is_superuser)
def admin_panel(request):
    """Vista del panel de administración centralizado"""
    return render(request, 'admin_panel.html')
