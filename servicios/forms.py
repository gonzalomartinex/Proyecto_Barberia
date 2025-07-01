from django import forms
from .models import Servicio
import os
from django.conf import settings

class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['nombre', 'imagen', 'descripcion', 'precio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'descripcion':
                field.widget.attrs['class'] = 'form-control bg-light border-2 border-warning rounded-4'
                field.widget.attrs['rows'] = 5
                field.widget.attrs['style'] = 'resize:vertical; min-height:120px;'
            elif field.widget.__class__.__name__ == 'ClearableFileInput':
                field.widget.attrs['class'] = 'form-control form-control-sm bg-light border-2 border-warning rounded-pill'
            else:
                field.widget.attrs['class'] = 'form-control bg-light border-2 border-warning rounded-pill'
        # Cambiar el texto del checkbox de imagen
        if 'imagen' in self.fields:
            self.fields['imagen'].widget.attrs['accept'] = 'image/*'
            self.fields['imagen'].widget.clear_checkbox_label = 'Eliminar imagen actual'

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Si se eliminó la imagen y no está en uso en otro modelo, eliminar el archivo físico
        if self.cleaned_data.get('imagen') is False:
            old_image = self.instance.imagen
            if old_image:
                # Verificar si la imagen está en uso en otros servicios
                from .models import Servicio
                count = Servicio.objects.filter(imagen=old_image.name).exclude(pk=self.instance.pk).count()
                # Aquí puedes agregar lógica para otros modelos (productos, usuarios) si es necesario
                if count == 0:
                    image_path = os.path.join(settings.MEDIA_ROOT, old_image.name)
                    if os.path.exists(image_path):
                        os.remove(image_path)
            # Asignar imagen default
            instance.imagen = 'Default/noimage.png'
        if commit:
            instance.save()
        return instance
