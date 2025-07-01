from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, time
from usuarios.models import Barbero
from servicios.models import Servicio
from turnos.models import Turno

class Command(BaseCommand):
    help = 'Crea turnos de ejemplo para hoy, de 13:00 a 19:00, cada 45 minutos, para todos los barberos y servicios.'

    def handle(self, *args, **kwargs):
        hoy = timezone.localdate()
        hora_inicio = time(13, 0)
        hora_fin = time(19, 0)
        duracion = timedelta(minutes=45)
        barberos = Barbero.objects.all()
        servicios = Servicio.objects.all()
        if not barberos.exists() or not servicios.exists():
            self.stdout.write(self.style.ERROR('Debe haber al menos un barbero y un servicio en la base de datos.'))
            return
        for barbero in barberos:
            for servicio in servicios:
                hora_actual = datetime.combine(hoy, hora_inicio)
                hora_limite = datetime.combine(hoy, hora_fin)
                while hora_actual <= hora_limite:
                    if not Turno.objects.filter(barbero=barbero, servicio=servicio, fecha_hora=hora_actual).exists():
                        Turno.objects.create(
                            barbero=barbero,
                            servicio=servicio,
                            fecha_hora=hora_actual,
                            estado='disponible'
                        )
                    hora_actual += duracion
        self.stdout.write(self.style.SUCCESS('Turnos creados correctamente.'))
