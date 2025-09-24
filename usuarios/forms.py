from django import forms
from .models import Barbero, RedSocial, Usuario
from django.forms import modelformset_factory
import os
from django.conf import settings

class DateWidget(forms.DateInput):
    """Widget personalizado para fechas que maneja mejor los valores iniciales"""
    
    def __init__(self, attrs=None):
        default_attrs = {'type': 'date', 'class': 'form-control bg-light border-2 border-warning rounded-pill'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)
    
    def format_value(self, value):
        """Asegura que el valor se formatee correctamente para el input HTML5"""
        if value is None:
            return ''
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return str(value)

class BarberoForm(forms.ModelForm):
    class Meta:
        model = Barbero
        fields = ['nombre', 'foto', 'fecha_nacimiento', 'bio', 'telefono', 'dni']
        widgets = {
            'fecha_nacimiento': DateWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar labels descriptivos
        self.fields['nombre'].label = 'Nombre completo'
        self.fields['foto'].label = 'Foto del barbero'
        self.fields['fecha_nacimiento'].label = 'Fecha de nacimiento'
        self.fields['bio'].label = 'Biografía / Descripción'
        self.fields['telefono'].label = 'Teléfono'
        self.fields['dni'].label = 'DNI'
        
        # Configurar placeholders y estilos
        self.fields['nombre'].widget.attrs.update({
            'placeholder': 'Ej: Juan Pérez',
            'class': 'form-control bg-light border-2 border-warning rounded-pill'
        })
        self.fields['telefono'].widget.attrs.update({
            'placeholder': 'Ej: +54 9 351 123-4567',
            'class': 'form-control bg-light border-2 border-warning rounded-pill'
        })
        self.fields['dni'].widget.attrs.update({
            'placeholder': 'Ej: 12345678',
            'class': 'form-control bg-light border-2 border-warning rounded-pill'
        })
        self.fields['bio'].widget.attrs.update({
            'placeholder': 'Describe la experiencia y especialidades del barbero...',
            'rows': 4,
            'class': 'form-control bg-light border-2 border-warning rounded'
        })
        
        # Configurar el campo de foto
        if 'foto' in self.fields:
            self.fields['foto'].widget.attrs.update({
                'accept': 'image/*',
                'class': 'form-control form-control-sm bg-light border-2 border-warning rounded-pill'
            })
            self.fields['foto'].widget.clear_checkbox_label = 'Eliminar imagen actual'
            self.fields['foto'].help_text = 'Formatos permitidos: JPG, PNG, WEBP, GIF. Tamaño máximo: 5MB'

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

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'email', 'telefono', 'foto_perfil']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar labels
        self.fields['nombre'].label = 'Nombre'
        self.fields['apellido'].label = 'Apellido'
        self.fields['email'].label = 'Correo electrónico'
        self.fields['telefono'].label = 'Teléfono'
        self.fields['foto_perfil'].label = 'Foto de perfil'
        
        # Configurar placeholders
        self.fields['nombre'].widget.attrs.update({'placeholder': 'Tu nombre'})
        self.fields['apellido'].widget.attrs.update({'placeholder': 'Tu apellido'})
        self.fields['email'].widget.attrs.update({'placeholder': 'tu@email.com'})
        self.fields['telefono'].widget.attrs.update({'placeholder': '+54 9 351 123-4567'})
        
        # Help text para la foto
        self.fields['foto_perfil'].help_text = 'Formatos permitidos: JPG, PNG, WEBP, GIF. Tamaño máximo: 5MB'

class CambiarContrasenaForm(forms.Form):
    """Formulario para cambiar contraseña desde el perfil del usuario"""
    
    contrasena_actual = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña actual'
        }),
        help_text='Para cambiar tu contraseña, primero confirma la actual.'
    )
    
    nueva_contrasena = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu nueva contraseña'
        }),
        min_length=4,
        help_text='La contraseña debe tener al menos 4 caracteres.'
    )
    
    confirmar_contrasena = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repite tu nueva contraseña'
        }),
        help_text='Vuelve a escribir la nueva contraseña para confirmar.'
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Agregar validaciones adicionales para la nueva contraseña
        self.fields['nueva_contrasena'].help_text = (
            'Recomendaciones para una contraseña segura:\n'
            '• Mínimo 8 caracteres (obligatorio: al menos 4)\n'
            '• Al menos una letra mayúscula\n'
            '• Al menos una letra minúscula\n'
            '• Al menos un número\n'
            '• Puede incluir símbolos (!@#$%^&*)'
        )

    def clean_contrasena_actual(self):
        contrasena_actual = self.cleaned_data.get('contrasena_actual')
        if not self.user.check_password(contrasena_actual):
            raise forms.ValidationError('La contraseña actual no es correcta.')
        return contrasena_actual

    def clean_nueva_contrasena(self):
        nueva_contrasena = self.cleaned_data.get('nueva_contrasena')
        
        if not nueva_contrasena:
            return nueva_contrasena
            
        # Solo validar longitud mínima como requisito obligatorio
        if len(nueva_contrasena) < 4:
            raise forms.ValidationError('La contraseña debe tener al menos 4 caracteres.')
        
        # Las demás validaciones son solo recomendaciones que se manejan en el frontend
        return nueva_contrasena

    def clean(self):
        cleaned_data = super().clean()
        nueva_contrasena = cleaned_data.get('nueva_contrasena')
        confirmar_contrasena = cleaned_data.get('confirmar_contrasena')

        if nueva_contrasena and confirmar_contrasena:
            if nueva_contrasena != confirmar_contrasena:
                self.add_error('confirmar_contrasena', 'Las contraseñas nuevas no coinciden.')
        
        return cleaned_data
