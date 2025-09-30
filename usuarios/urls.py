from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import PerfilUsuarioView, cambiar_estado_usuario, gestionar_redes_barbero, gestionar_usuarios, editar_usuario_admin, cancelar_turno_usuario

urlpatterns = [
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Aquí se agregarán endpoints personalizados de usuario
    path('auth/perfil/', PerfilUsuarioView.as_view(), name='perfil_usuario'),
    path('usuarios/<int:pk>/cambiar-estado/', cambiar_estado_usuario, name='cambiar-estado-usuario'),
    path('registro/', views.registro_usuario, name='registro'),
    path('barberos/<int:barbero_id>/redes/', gestionar_redes_barbero, name='gestionar-redes-barbero'),
    path('gestionar/', gestionar_usuarios, name='gestionar-usuarios'),
    path('editar/<int:user_id>/', editar_usuario_admin, name='editar-usuario-admin'),
    path('perfil/editar/', views.editar_perfil_usuario, name='editar-perfil'),
    path('perfil/cambiar-contrasena/', views.cambiar_contrasena, name='cambiar-contrasena'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('perfil/cancelar-turno/<int:turno_id>/', cancelar_turno_usuario, name='cancelar-turno-usuario'),
]
