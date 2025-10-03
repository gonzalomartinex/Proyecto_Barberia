from django.core.management.base import BaseCommand
from django.utils import timezone
from turnos.models import Turno
from datetime import timedelta

class Command(BaseCommand):
    help = 'Marca como expirados los turnos disponibles que ya pasaron su fecha/hora'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué turnos se marcarían como expirados sin hacer cambios',
        )

    def handle(self, *args, **options):
        # Obtener la hora actual
        now = timezone.now()
        
        # Buscar turnos disponibles que ya pasaron
        turnos_expirados = Turno.objects.filter(
            estado='disponible',
            fecha_hora__lt=now
        )
        
        count = turnos_expirados.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No hay turnos para marcar como expirados.')
            )
            return
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Se marcarían {count} turnos como expirados:')
            )
            for turno in turnos_expirados:
                self.stdout.write(f'  - {turno.fecha_hora} - {turno.barbero} - {turno.servicio}')
        else:
            # Marcar como expirados
            updated = turnos_expirados.update(estado='expirado')
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ {updated} turnos marcados como expirados.')
            )
            
            # Mostrar detalles de los turnos marcados
            for turno in Turno.objects.filter(
                estado='expirado',
                fecha_hora__lt=now
            ).order_by('-fecha_hora')[:10]:  # Mostrar los últimos 10
                self.stdout.write(f'  - {turno.fecha_hora} - {turno.barbero} - {turno.servicio or "Sin servicio"}')
                
            if updated > 10:
                self.stdout.write(f'  ... y {updated - 10} más')
