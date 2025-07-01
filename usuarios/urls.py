from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import PerfilUsuarioView, cambiar_estado_usuario, gestionar_redes_barbero

urlpatterns = [
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Aquí se agregarán endpoints personalizados de usuario
    path('auth/perfil/', PerfilUsuarioView.as_view(), name='perfil_usuario'),
    path('usuarios/<int:pk>/cambiar-estado/', cambiar_estado_usuario, name='cambiar-estado-usuario'),
    path('registro/', views.registro_usuario, name='registro'),
    path('barberos/<int:barbero_id>/redes/', gestionar_redes_barbero, name='gestionar-redes-barbero'),
]
