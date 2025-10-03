"""
URL configuration for BarberiaApp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from django.views.generic import TemplateView
from usuarios.views import barberos_list, barbero_perfil, cargar_trabajo_barbero, eliminar_trabajo_barbero, registrar_barbero, editar_barbero, eliminar_barbero
from turnos.views import reservar_turno, reservar_turno_form
from django.contrib.auth.views import LoginView, LogoutView
from usuarios.views import perfil_usuario
from django.contrib.auth import views as auth_views
from servicios import views as servicios_views
from django.conf import settings
from django.conf.urls.static import static
from productos.models import Producto
from django.shortcuts import render
from django.http import HttpResponseRedirect
from BarberiaApp.views import index, editar_carrusel, admin_panel
from django.contrib.auth import logout
from django.shortcuts import redirect

def productos_list(request):
    productos = Producto.objects.all()
    return render(request, 'productos.html', {'productos': productos})

def custom_logout(request):
    from django.contrib import messages
    logout(request)
    messages.success(request, 'Sesión cerrada correctamente.')
    return redirect('/')

urlpatterns = [
    path('', index, name='inicio'),
    path('admin/', admin.site.urls),
    path('api/', include('usuarios.urls')),
    path('api/', include('servicios.urls')),
    path('api/', include('productos.urls')),
    path('api/', include('turnos.urls')),
    path('api/', include('administracion.urls')),
    path('barberos/', barberos_list, name='barberos-list'),
    path('barberos/<int:pk>/', barbero_perfil, name='barbero-perfil'),
    path('turnos/', reservar_turno_form, name='turnos-reserva-form'),
    path('perfil/', perfil_usuario, name='perfil-usuario'),
    path('turnos/reservar/<int:turno_id>/', reservar_turno, name='reservar-turno'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('servicios/', servicios_views.ServicioListView, name='servicios-list'),
    path('barberos/<int:barbero_id>/cargar-trabajo/', cargar_trabajo_barbero, name='cargar-trabajo-barbero'),
    path('barberos/trabajo/<int:trabajo_id>/eliminar/', eliminar_trabajo_barbero, name='eliminar-trabajo-barbero'),
    path('barberos/registrar/', registrar_barbero, name='registrar-barbero'),
    path('barberos/<int:pk>/editar/', editar_barbero, name='editar-barbero'),
    path('barberos/<int:pk>/eliminar/', eliminar_barbero, name='eliminar-barbero'),
    path('usuarios/', include('usuarios.urls')),  # Asegura inclusión de rutas de usuarios
    path('productos/', productos_list, name='productos-list'),
    path('administracion/', include('administracion.urls')),  # Asegura inclusión de rutas de administración
    path('carrusel/editar/', editar_carrusel, name='editar-carrusel'),
    path('admin-panel/', admin_panel, name='admin-panel'),
    path('cursos/', include('cursos.urls')),
]

# Servir archivos media solo en desarrollo
# En producción con Cloudinary, las imágenes se sirven desde Cloudinary
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
