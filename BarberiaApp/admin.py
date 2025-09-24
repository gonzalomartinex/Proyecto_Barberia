from django.contrib import admin
from .models import CarouselImage

@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ('orden', 'imagen')
    list_editable = ('orden',)
    list_display_links = ('imagen',)
    ordering = ('orden',)
