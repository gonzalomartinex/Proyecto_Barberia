from django.urls import path
from . import views
from .views import (
    RegistroServiciosListCreateView, RegistroServiciosRetrieveUpdateDestroyView,
    estadisticas_servicios_mas_pedidos, estadisticas_ingresos_por_barbero, estadisticas_cantidad_turnos
)

urlpatterns = [
    # Endpoints de administración y reportes
    path('registros-servicios/', RegistroServiciosListCreateView.as_view(), name='registroservicios-list-create'),
    path('registros-servicios/<int:pk>/', RegistroServiciosRetrieveUpdateDestroyView.as_view(), name='registroservicios-detail'),

    # Endpoints de estadísticas
    path('estadisticas/servicios-mas-pedidos/', estadisticas_servicios_mas_pedidos, name='estadisticas-servicios-mas-pedidos'),
    path('estadisticas/ingresos-por-barbero/', estadisticas_ingresos_por_barbero, name='estadisticas-ingresos-por-barbero'),
    path('estadisticas/cantidad-turnos/', estadisticas_cantidad_turnos, name='estadisticas-cantidad-turnos'),

    # Ruta para la administración de turnos
    path('turnos/', views.administracion_turnos, name='administracion-turnos'),
    path('agregar-turnos/', views.agregar_turnos, name='agregar-turnos'),
    path('turnos/cancelar/', views.cancelar_turno_admin, name='cancelar-turno-admin'),
    path('turnos/cambiar-estado/', views.cambiar_estado_turno_admin, name='cambiar-estado-turno-admin'),
    path('turno/<int:turno_id>/datos/', views.obtener_datos_turno_admin, name='obtener-datos-turno-admin'),
    path('turno/editar/', views.editar_turno_admin, name='editar-turno-admin'),
    path('turnos/archivar/', views.archivar_turnos_vista, name='archivar-turnos'),
    path('turnos/archivos/', views.listar_archivos_excel, name='listar-archivos-excel'),
    path('turnos/descargar/<str:nombre_archivo>/', views.descargar_archivo_excel, name='descargar-archivo-excel'),
]
