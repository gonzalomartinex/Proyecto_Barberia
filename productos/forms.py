from django import forms
from .models import Producto
import os
from django.conf import settings

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'imagen', 'precio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ == 'ClearableFileInput':
                field.widget.attrs['class'] = 'form-control form-control-sm bg-light border-2 border-warning rounded-pill'
            else:
                field.widget.attrs['class'] = 'form-control bg-light border-2 border-warning rounded-pill'
        if 'imagen' in self.fields:
            self.fields['imagen'].widget.attrs['accept'] = 'image/*'
            self.fields['imagen'].widget.clear_checkbox_label = 'Eliminar imagen actual'

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('imagen') is False:
            old_image = self.instance.imagen
            if old_image:
                from .models import Producto
                count = Producto.objects.filter(imagen=old_image.name).exclude(pk=self.instance.pk).count()
                if count == 0:
                    image_path = os.path.join(settings.MEDIA_ROOT, old_image.name)
                    if os.path.exists(image_path):
                        os.remove(image_path)
            instance.imagen = 'Default/noimage.png'
        if commit:
            instance.save()
        return instance
