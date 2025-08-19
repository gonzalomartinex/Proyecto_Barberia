from django import forms
from .models import CarouselImage

class CarouselImageForm(forms.ModelForm):
    class Meta:
        model = CarouselImage
        fields = ['imagen']
