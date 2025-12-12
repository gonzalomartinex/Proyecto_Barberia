from django.apps import AppConfig


class ProductosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'productos'
    
    def ready(self):
        """
        Importa las señales cuando la aplicación esté lista
        """
        import productos.models  # Esto cargará las señales definidas en models.py
