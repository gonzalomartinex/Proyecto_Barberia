from django.apps import AppConfig

class BarberiaappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'BarberiaApp'
    
    def ready(self):
        # Importar señales para que se registren automáticamente
        import utils.cloudinary_cleanup
