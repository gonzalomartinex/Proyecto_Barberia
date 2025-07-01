from django.urls import path
from . import views
from .views import ProductoListCreateView, ProductoRetrieveUpdateDestroyView

urlpatterns = [
    # Endpoints de productos
    path('productos/', ProductoListCreateView.as_view(), name='producto-list-create'),
    path('productos/<int:pk>/', ProductoRetrieveUpdateDestroyView.as_view(), name='producto-detail'),
    # Vistas para el frontend
    path('productos/lista/', views.ProductoListView, name='producto-lista'),
    path('productos/agregar/', views.ProductoCreateView.as_view(), name='producto-create'),
    path('productos/<int:pk>/editar/', views.ProductoUpdateView.as_view(), name='producto-update'),
    path('productos/<int:pk>/eliminar/', views.ProductoDeleteView.as_view(), name='producto-delete'),
]
