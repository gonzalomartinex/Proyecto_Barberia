from django import forms
from .models import Barbero, RedSocial
from django.forms import modelformset_factory
import os
from django.conf import settings

class BarberoForm(forms.ModelForm):
    class Meta:
        model = Barbero
        fields = ['nombre', 'foto', 'fecha_nacimiento', 'bio', 'telefono', 'dni']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'bio':
                field.widget.attrs['class'] = 'form-control bg-light border-2 border-warning rounded-4'
                field.widget.attrs['rows'] = 5
                field.widget.attrs['style'] = 'resize:vertical; min-height:120px;'
            elif field.widget.__class__.__name__ == 'ClearableFileInput':
                field.widget.attrs['class'] = 'form-control form-control-sm bg-light border-2 border-warning rounded-pill'
            else:
                field.widget.attrs['class'] = 'form-control bg-light border-2 border-warning rounded-pill'
        # Cambiar el texto del checkbox de imagen
        if 'foto' in self.fields:
            self.fields['foto'].widget.attrs['accept'] = 'image/*'
            self.fields['foto'].widget.clear_checkbox_label = 'Eliminar imagen actual'

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Si se eliminó la imagen y no está en uso en otro barbero, eliminar el archivo físico
        if self.cleaned_data.get('foto') is False:
            old_image = self.instance.foto
            if old_image:
                from .models import Barbero
                count = Barbero.objects.filter(foto=old_image.name).exclude(pk=self.instance.pk).count()
                if count == 0:
                    image_path = os.path.join(settings.MEDIA_ROOT, old_image.name)
                    if os.path.exists(image_path):
                        os.remove(image_path)
            # Asignar imagen default
            instance.foto = 'Default/noimage.png'
        if commit:
            instance.save()
        return instance

def get_redsocial_formset(extra=1):
    return modelformset_factory(
        RedSocial,
        fields=("url", "nombre"),
        extra=extra,
        can_delete=True
    )
