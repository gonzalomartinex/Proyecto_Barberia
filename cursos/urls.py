from django.urls import path
from . import views

urlpatterns = [
    path('', views.cursos_list, name='cursos-list'),
    path('crear/', views.crear_curso, name='crear-curso'),
    path('<int:pk>/editar/', views.editar_curso, name='editar-curso'),
    path('<int:pk>/eliminar/', views.eliminar_curso, name='eliminar-curso'),
]
