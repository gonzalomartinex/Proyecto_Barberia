from django.urls import path
from . import views
from .views import TurnoListCreateView, TurnoRetrieveUpdateDestroyView, cambiar_estado_turno, reservar_turno, reservar_turno_form

urlpatterns = [
    # Endpoints de turnos
    path('turnos/', TurnoListCreateView.as_view(), name='turno-list-create'),
    path('turnos/<int:pk>/', TurnoRetrieveUpdateDestroyView.as_view(), name='turno-detail'),
    path('turnos/<int:pk>/cambiar-estado/', cambiar_estado_turno, name='cambiar-estado-turno'),
    path('turnos/reservar/<int:turno_id>/', reservar_turno, name='reservar-turno'),
    path('turnos/reservar/', reservar_turno_form, name='reservar-turno-form'),
]
