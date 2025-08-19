import os
from django.conf import settings
from django.shortcuts import render
from pathlib import Path
from .models import CarouselImage
from django.contrib.auth.decorators import user_passes_test
from .forms import CarouselImageForm
from django.shortcuts import redirect

def index(request):
    carousel_images = CarouselImage.objects.order_by('orden')
    return render(request, 'index.html', {'carousel_images': [img.imagen.url for img in carousel_images]})

@user_passes_test(lambda u: u.is_superuser)
def editar_carrusel(request):
    images = list(CarouselImage.objects.order_by('orden'))
    if request.method == 'POST':
        if 'add' in request.POST:
            form = CarouselImageForm(request.POST, request.FILES)
            if form.is_valid():
                # Asignar orden al final
                last_order = images[-1].orden + 1 if images else 0
                new_img = form.save(commit=False)
                new_img.orden = last_order
                new_img.save()
                return redirect('editar-carrusel')
        elif 'delete' in request.POST:
            img_id = int(request.POST.get('delete'))
            CarouselImage.objects.filter(id=img_id).delete()
            # Reordenar después de eliminar
            imgs = CarouselImage.objects.order_by('orden')
            for idx, img in enumerate(imgs):
                img.orden = idx
                img.save()
            return redirect('editar-carrusel')
        elif 'move_left' in request.POST or 'move_right' in request.POST:
            img_id = int(request.POST.get('move_left') or request.POST.get('move_right'))
            idx = next((i for i, img in enumerate(images) if img.id == img_id), None)
            if idx is not None:
                if 'move_left' in request.POST and idx > 0:
                    images[idx].orden, images[idx-1].orden = images[idx-1].orden, images[idx].orden
                    images[idx].save()
                    images[idx-1].save()
                elif 'move_right' in request.POST and idx < len(images)-1:
                    images[idx].orden, images[idx+1].orden = images[idx+1].orden, images[idx].orden
                    images[idx].save()
                    images[idx+1].save()
            return redirect('editar-carrusel')
    else:
        form = CarouselImageForm()
    images = CarouselImage.objects.order_by('orden')
    return render(request, 'editar_carrusel.html', {'images': images, 'form': form})
