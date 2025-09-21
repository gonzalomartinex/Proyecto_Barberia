from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from turnos.models import Turno
import pandas as pd
import os
from django.conf import settings
from pathlib import Path

class Command(BaseCommand):
    help = 'Archiva turnos expirados en Excel y los elimina de la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué turnos se procesarían sin ejecutar cambios',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Días después del turno para considerar expirado (por defecto: 30)',
        )
        parser.add_argument(
            '--estados',
            nargs='+',
            default=None,
            help='Estados de turnos a archivar (ej: --estados completado cancelado)',
        )
        parser.add_argument(
            '--incluir-disponibles',
            action='store_false',
            dest='excluir_disponibles',
            help='Incluir turnos disponibles (por defecto se excluyen los disponibles)',
        )
        parser.add_argument(
            '--solo-ocupados',
            action='store_true',
            help='Archivar solo turnos ocupados/completados (ignora disponibles y cancelados)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        dias_expiracion = options['days']
        estados_incluir = options['estados']
        solo_ocupados = options['solo_ocupados']
        excluir_disponibles = options['excluir_disponibles']
        
        # Mostrar parámetros recibidos (solo en verbosity alta)
        if options.get('verbosity', 1) >= 2:
            self.stdout.write(f'DEBUG: Parámetros recibidos:')
            self.stdout.write(f'  - Días: {dias_expiracion}')
            self.stdout.write(f'  - Estados: {estados_incluir}')
            self.stdout.write(f'  - Solo ocupados: {solo_ocupados}')
            self.stdout.write(f'  - Excluir disponibles: {excluir_disponibles}')
        
        # Determinar qué estados incluir
        if solo_ocupados:
            # Si se especifica --solo-ocupados, solo incluir ocupados y completados
            estados_incluir = ['ocupado', 'completado']
        elif estados_incluir:
            # Si se especificaron estados específicos, usarlos tal como están
            pass  # estados_incluir ya tiene los valores correctos
        elif excluir_disponibles:
            # Si no se especificaron estados y excluir_disponibles es True (por defecto)
            # entonces usar los estados por defecto excluyendo disponible
            estados_incluir = ['ocupado', 'completado', 'cancelado']
        else:
            # Incluir todos los estados si no se excluyen disponibles
            estados_incluir = ['disponible', 'ocupado', 'completado', 'cancelado']
        
        # Mostrar estados finales (solo en verbosity alta)
        if options.get('verbosity', 1) >= 2:
            self.stdout.write(f'DEBUG: Estados finales a incluir: {estados_incluir}')
        
        # Fecha límite (ej: hace 30 días)
        fecha_limite = timezone.now() - timedelta(days=dias_expiracion)
        
        # Mostrar fecha límite (solo en verbosity alta)
        if options.get('verbosity', 1) >= 2:
            self.stdout.write(f'DEBUG: Fecha límite calculada: {fecha_limite.strftime("%Y-%m-%d %H:%M:%S")}')
        
        # Buscar turnos expirados con los estados especificados (ordenados por fecha)
        turnos_expirados = Turno.objects.filter(
            fecha_hora__lt=fecha_limite,
            estado__in=estados_incluir
        ).select_related('barbero', 'servicio', 'cliente').order_by('fecha_hora')
        
        # Debug: mostrar consulta SQL (solo en verbosity muy alta)
        if options.get('verbosity', 1) >= 3:
            self.stdout.write(f'DEBUG: Query SQL: {turnos_expirados.query}')
            self.stdout.write(f'DEBUG: Total turnos en DB: {Turno.objects.count()}')
            self.stdout.write(f'DEBUG: Turnos antes de fecha límite: {Turno.objects.filter(fecha_hora__lt=fecha_limite).count()}')
            self.stdout.write(f'DEBUG: Turnos con estados específicos: {Turno.objects.filter(estado__in=estados_incluir).count()}')
        
        if not turnos_expirados.exists():
            self.stdout.write(
                self.style.SUCCESS('No hay turnos expirados para procesar.')
            )
            return
        
        self.stdout.write(
            f'Encontrados {turnos_expirados.count()} turnos expirados '
            f'(anteriores al {fecha_limite.strftime("%Y-%m-%d %H:%M")})'
        )
        self.stdout.write(f'Estados incluidos: {", ".join(estados_incluir)}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN - No se realizarán cambios'))
            for turno in turnos_expirados[:5]:  # Mostrar solo los primeros 5
                self.stdout.write(
                    f'- {turno.fecha_hora.strftime("%Y-%m-%d %H:%M")} | '
                    f'{turno.barbero.nombre if turno.barbero else "Sin barbero"} | '
                    f'{turno.servicio.nombre if turno.servicio else "Sin servicio"} | '
                    f'{turno.estado}'
                )
            if turnos_expirados.count() > 5:
                self.stdout.write(f'... y {turnos_expirados.count() - 5} más')
            return
        
        # Crear DataFrame con los datos de los turnos (formato simple)
        datos_turnos = []
        for turno in turnos_expirados:
            datos_turnos.append({
                'ID': turno.id,
                'Fecha': turno.fecha_hora.strftime('%Y-%m-%d'),
                'Hora': turno.fecha_hora.strftime('%H:%M'),
                'Barbero': turno.barbero.nombre if turno.barbero else 'Sin barbero',
                'Cliente': f'{turno.cliente.nombre} {turno.cliente.apellido}' if turno.cliente else 'Sin cliente',
                'Servicio': turno.servicio.nombre if turno.servicio else 'Sin servicio',
                'Precio': f"${turno.servicio.precio:,.2f}" if turno.servicio and turno.servicio.precio else '$0,00',
                'Estado': turno.estado,
                'Fecha_Archivado': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Crear directorio de archivos si no existe
        archivos_dir = Path(settings.MEDIA_ROOT) / 'archivos_turnos'
        archivos_dir.mkdir(exist_ok=True)
        
        # Generar ID único del registro (basado en timestamp)
        timestamp_id = int(timezone.now().timestamp())
        fecha_actual = timezone.now()
        fecha_str = fecha_actual.strftime('%d-%m-%Y')
        hora_str = fecha_actual.strftime('%H-%M-%S')
        cantidad_turnos = turnos_expirados.count()
        
        # Crear nombre del archivo: ID--fecha--hora--cantidad
        nombre_archivo = f'{timestamp_id}--{fecha_str}--{hora_str}--{cantidad_turnos}-turnos.xlsx'
        ruta_archivo = archivos_dir / nombre_archivo
        
        try:
            # Crear DataFrame de turnos (ordenados por fecha)
            df_turnos = pd.DataFrame(datos_turnos)
            
            # === CREAR ESTADÍSTICAS DE BARBEROS ===
            estadisticas_barberos = self._calcular_estadisticas_barberos(turnos_expirados)
            df_estadisticas = pd.DataFrame(estadisticas_barberos)
            
            # === CREAR ESTADÍSTICAS GENERALES DE LA BARBERÍA ===
            estadisticas_barberia = self._calcular_estadisticas_barberia(turnos_expirados)
            df_barberia = pd.DataFrame(estadisticas_barberia)
            
            # Crear archivo Excel con múltiples hojas
            with pd.ExcelWriter(ruta_archivo, engine='openpyxl') as writer:
                # Hoja 1: Turnos archivados (ordenados por fecha)
                df_turnos.to_excel(writer, sheet_name='Turnos_Archivados', index=False)
                
                # Hoja 2: Estadísticas de barberos
                if not df_estadisticas.empty:
                    df_estadisticas.to_excel(writer, sheet_name='Estadisticas_Barberos', index=False)
                
                # Hoja 3: Estadísticas generales de la barbería
                if not df_barberia.empty:
                    df_barberia.to_excel(writer, sheet_name='Resumen_Barberia', index=False)
                
                # Ajustar ancho de columnas
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_name = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = (max_length + 2) * 1.2
                        worksheet.column_dimensions[column_name].width = min(adjusted_width, 50)
            
            # Actualizar archivo maestro
            archivo_maestro = archivos_dir / 'turnos_archivados_historial.xlsx'
            
            if archivo_maestro.exists():
                try:
                    df_existente = pd.read_excel(archivo_maestro)
                    df_combinado = pd.concat([df_existente, df_turnos], ignore_index=True)
                    df_combinado.to_excel(archivo_maestro, index=False)
                    self.stdout.write(
                        self.style.SUCCESS(f'Datos agregados al archivo maestro: {archivo_maestro}')
                    )
                except Exception as e:
                    # Si hay error leyendo el archivo existente, crear uno nuevo
                    df_turnos.to_excel(archivo_maestro, index=False)
                    self.stdout.write(
                        self.style.WARNING(f'Archivo maestro recreado: {archivo_maestro}')
                    )
            else:
                # Crear archivo maestro por primera vez
                df_turnos.to_excel(archivo_maestro, index=False)
                self.stdout.write(
                    self.style.SUCCESS(f'Archivo maestro creado: {archivo_maestro}')
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'Archivo individual creado: {ruta_archivo}')
            )
            
            # Eliminar turnos de la base de datos
            cantidad_eliminados = turnos_expirados.count()
            turnos_expirados.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Proceso completado:\n'
                    f'   - {cantidad_eliminados} turnos archivados en Excel\n'
                    f'   - {cantidad_eliminados} turnos eliminados de la base de datos\n'
                    f'   - Estados procesados: {", ".join(estados_incluir)}\n'
                    f'   - Archivo: {ruta_archivo}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al procesar turnos: {str(e)}')
            )

    def _calcular_estadisticas_barberos(self, turnos_queryset):
        """
        Calcula estadísticas detalladas de cada barbero basándose en los turnos archivados
        """
        from collections import defaultdict
        from datetime import timedelta
        
        # Diccionario para acumular datos por barbero
        stats_barberos = defaultdict(lambda: {
            'servicios_realizados': 0,
            'servicios_por_tipo': defaultdict(int),
            'dinero_generado': 0.0,
            'turnos_completados': 0,
            'dias_activo': set()
        })
        
        for turno in turnos_queryset:
            barbero_nombre = turno.barbero.nombre if turno.barbero else 'Sin barbero'
            stats = stats_barberos[barbero_nombre]
            
            # Contar servicios realizados (solo completados y ocupados)
            if turno.estado in ['completado', 'ocupado']:
                stats['servicios_realizados'] += 1
                stats['turnos_completados'] += 1
                
                # Dinero generado
                if turno.servicio and turno.servicio.precio:
                    stats['dinero_generado'] += float(turno.servicio.precio)
                
                # Servicios por tipo
                if turno.servicio:
                    stats['servicios_por_tipo'][turno.servicio.nombre] += 1
            
            # Días únicos trabajados (solo para servicios completados/ocupados)
            if turno.estado in ['completado', 'ocupado']:
                stats['dias_activo'].add(turno.fecha_hora.date())
        
        # Convertir a lista de diccionarios para DataFrame
        estadisticas_finales = []
        for barbero, stats in stats_barberos.items():
            # Crear string de servicios por tipo
            servicios_detalle = ', '.join([f'{servicio}: {cantidad}' 
                                         for servicio, cantidad in stats['servicios_por_tipo'].items()])
            
            estadisticas_finales.append({
                'Barbero': barbero,
                'Servicios_Realizados': stats['servicios_realizados'],
                'Servicios_por_Tipo': servicios_detalle or 'Ninguno',
                'Dinero_Generado': f"${stats['dinero_generado']:,.2f}",
                'Turnos_Completados': stats['turnos_completados'],
                'Dias_Activos': len(stats['dias_activo'])
            })
        
        # Ordenar por dinero generado (descendente)
        estadisticas_finales.sort(key=lambda x: float(x['Dinero_Generado'].replace('$', '').replace(',', '')), reverse=True)
        
        return estadisticas_finales

    def _calcular_estadisticas_barberia(self, turnos_queryset):
        """
        Calcula estadísticas generales de toda la barbería basándose en los turnos archivados
        """
        from collections import defaultdict
        
        # Contadores generales
        total_servicios = 0
        total_dinero = 0.0
        servicios_por_tipo = defaultdict(int)
        estados_count = defaultdict(int)
        barberos_activos = set()
        clientes_atendidos = set()
        
        # Fechas
        primer_turno = None
        ultimo_turno = None
        dias_con_actividad = set()
        
        # Procesar cada turno
        for turno in turnos_queryset:
            # Contar por estado
            estados_count[turno.estado] += 1
            
            # Solo servicios realizados (completados y ocupados)
            if turno.estado in ['completado', 'ocupado']:
                total_servicios += 1
                
                # Dinero generado
                if turno.servicio and turno.servicio.precio:
                    total_dinero += float(turno.servicio.precio)
                
                # Servicios por tipo
                if turno.servicio:
                    servicios_por_tipo[turno.servicio.nombre] += 1
                
                # Barberos activos
                if turno.barbero:
                    barberos_activos.add(turno.barbero.nombre)
                
                # Clientes atendidos
                if turno.cliente:
                    clientes_atendidos.add(f"{turno.cliente.nombre} {turno.cliente.apellido}")
                
                # Días con actividad
                dias_con_actividad.add(turno.fecha_hora.date())
            
            # Fechas generales
            if not primer_turno or turno.fecha_hora < primer_turno:
                primer_turno = turno.fecha_hora
            if not ultimo_turno or turno.fecha_hora > ultimo_turno:
                ultimo_turno = turno.fecha_hora
        
        # Calcular período
        periodo_archivado = ""
        if primer_turno and ultimo_turno:
            if primer_turno.date() == ultimo_turno.date():
                periodo_archivado = primer_turno.strftime('%d/%m/%Y')
            else:
                periodo_archivado = f"{primer_turno.strftime('%d/%m/%Y')} al {ultimo_turno.strftime('%d/%m/%Y')}"
        
        # Crear lista de servicios detallados
        servicios_detalle = ', '.join([f'{servicio}: {cantidad}' 
                                     for servicio, cantidad in sorted(servicios_por_tipo.items())])
        
        # Crear estadísticas finales
        estadisticas_barberia = [
            {
                'Metrica': 'Servicios Totales Realizados',
                'Valor': f'{total_servicios} servicios',
                'Detalle': servicios_detalle or 'Ninguno'
            },
            {
                'Metrica': 'Dinero Total Generado',
                'Valor': f'${total_dinero:,.2f}',
                'Detalle': f'Promedio por servicio: ${total_dinero/total_servicios:,.2f}' if total_servicios > 0 else 'N/A'
            },
            {
                'Metrica': 'Barberos Activos',
                'Valor': f'{len(barberos_activos)} barberos',
                'Detalle': ', '.join(sorted(barberos_activos)) if barberos_activos else 'Ninguno'
            },
            {
                'Metrica': 'Clientes Atendidos',
                'Valor': f'{len(clientes_atendidos)} clientes únicos',
                'Detalle': f'Promedio: {total_servicios/len(clientes_atendidos):,.1f} servicios por cliente' if len(clientes_atendidos) > 0 else 'N/A'
            },
            {
                'Metrica': 'Días con Actividad',
                'Valor': f'{len(dias_con_actividad)} días',
                'Detalle': f'Promedio: {total_servicios/len(dias_con_actividad):,.1f} servicios por día' if len(dias_con_actividad) > 0 else 'N/A'
            },
            {
                'Metrica': 'Período Archivado',
                'Valor': periodo_archivado,
                'Detalle': f'Total de registros procesados: {sum(estados_count.values())}'
            },
            {
                'Metrica': 'Distribución por Estado',
                'Valor': f'{len(estados_count)} estados diferentes',
                'Detalle': ', '.join([f'{estado}: {cantidad}' for estado, cantidad in sorted(estados_count.items())])
            }
        ]
        
        return estadisticas_barberia
