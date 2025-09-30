from django.urls import path
from . import views
from .views import TurnoListCreateView, TurnoRetrieveUpdateDestroyView, cambiar_estado_turno, reservar_turno, reservar_turno_form, marcar_notificacion_leida, listar_notificaciones, actualizar_precio_turno, obtener_datos_turno, editar_turno, marcar_todas_notificaciones_leidas

urlpatterns = [
    # Endpoints de turnos
    path('turnos/', TurnoListCreateView.as_view(), name='turno-list-create'),
    path('turnos/<int:pk>/', TurnoRetrieveUpdateDestroyView.as_view(), name='turno-detail'),
    path('turnos/<int:pk>/cambiar-estado/', cambiar_estado_turno, name='cambiar-estado-turno'),
    path('turnos/reservar/<int:turno_id>/', reservar_turno, name='reservar-turno'),
    path('turnos/reservar/', reservar_turno_form, name='reservar-turno-form'),
    path('turnos/actualizar-precio/', actualizar_precio_turno, name='actualizar-precio-turno'),
    # Endpoints de notificaciones
    path('notificaciones/<int:notificacion_id>/marcar-leida/', marcar_notificacion_leida, name='marcar-notificacion-leida'),
    path('notificaciones/marcar-todas-leidas/', marcar_todas_notificaciones_leidas, name='marcar-todas-notificaciones-leidas'),
    path('notificaciones/', listar_notificaciones, name='listar-notificaciones'),
]
