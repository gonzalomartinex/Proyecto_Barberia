from django.db import models
from usuarios.models import Usuario, Barbero
from servicios.models import Servicio

class Turno(models.Model):
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('ocupado', 'Ocupado'),
        ('cancelado', 'Cancelado'),
        ('completado', 'Completado'),
    ]
    cliente = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='turnos')
    barbero = models.ForeignKey(Barbero, on_delete=models.CASCADE, related_name='turnos')
    fecha_hora = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='disponible')
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='turnos', null=True, blank=True)
    precio_final = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Precio final del turno (puede ser diferente al precio del servicio)"
    )
    
    def __str__(self):
        return f"{self.fecha_hora} - {self.barbero} - {self.estado}"

class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('turno_reservado', 'Turno Reservado'),
        ('turno_cancelado', 'Turno Cancelado'),
        ('turno_completado', 'Turno Completado'),
        ('turno_modificado', 'Turno Modificado'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name='notificaciones')
    mensaje = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
    
    def __str__(self):
        from django.utils.timezone import localtime
        fecha_hora_local = localtime(self.turno.fecha_hora)
        return f"{self.get_tipo_display()} - {fecha_hora_local.strftime('%d/%m/%Y %H:%M')}"
    
    def get_mensaje_completo(self):
        """Genera un mensaje completo con todos los detalles del turno"""
        from django.utils.timezone import localtime
        
        # Convertir a hora local para mostrar correctamente
        fecha_hora_local = localtime(self.turno.fecha_hora)
        
        # Crear el formato con día de la semana en español
        dias_semana = {
            0: 'lunes',
            1: 'martes', 
            2: 'miércoles',
            3: 'jueves',
            4: 'viernes',
            5: 'sábado',
            6: 'domingo'
        }
        
        dia_semana = dias_semana[fecha_hora_local.weekday()]
        fecha_formateada = f"{fecha_hora_local.strftime('%d/%m/%Y')} ({dia_semana}) a las {fecha_hora_local.strftime('%H:%M')}"
        
        # Obtener nombre del cliente de forma segura
        if self.turno.cliente:
            cliente_nombre = f"{self.turno.cliente.nombre} {self.turno.cliente.apellido}"
        else:
            cliente_nombre = "Usuario eliminado"
        
        # Obtener nombre del barbero de forma segura
        barbero_nombre = self.turno.barbero.nombre if self.turno.barbero else "Barbero no disponible"
        
        if self.tipo == 'turno_reservado':
            return f"🔔 Nuevo turno reservado para el {fecha_formateada} con {barbero_nombre}. Cliente: {cliente_nombre}."
        elif self.tipo == 'turno_cancelado':
            return f"❌ Turno cancelado del {fecha_formateada} con {barbero_nombre}. Cliente: {cliente_nombre}."
        elif self.tipo == 'turno_completado':
            return f"✅ Turno completado del {fecha_formateada} con {barbero_nombre}. Cliente: {cliente_nombre}."
        elif self.tipo == 'turno_modificado':
            return f"🔄 Turno modificado del {fecha_formateada} con {barbero_nombre}. Cliente: {cliente_nombre}."
        return self.mensaje
