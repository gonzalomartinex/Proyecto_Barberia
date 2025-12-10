from django.urls import path
from . import views
from .views import ServicioListCreateView, ServicioRetrieveUpdateDestroyView

urlpatterns = [
    # Endpoints de servicios
    path('servicios/', ServicioListCreateView.as_view(), name='servicio-list-create'),
    path('servicios/<int:pk>/', ServicioRetrieveUpdateDestroyView.as_view(), name='servicio-detail'),
    # Vistas para el frontend
    path('servicios/lista/', views.ServicioListView, name='servicio-lista'),
    path('servicios/agregar/', views.ServicioCreateView.as_view(), name='servicio-create'),
    path('servicios/<int:pk>/editar/', views.ServicioUpdateView.as_view(), name='servicio-update'),
    path('servicios/<int:pk>/eliminar/', views.ServicioDeleteView.as_view(), name='servicio-delete'),
    # Reordenamiento
    path('servicios/reordenar/', views.reordenar_servicios, name='reordenar-servicios'),
]
