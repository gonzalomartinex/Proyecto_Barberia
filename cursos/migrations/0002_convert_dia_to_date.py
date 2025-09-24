from django.db import migrations, models
from django.utils import timezone
from datetime import datetime, timedelta

def convert_day_to_date(apps, schema_editor):
    """
    Convertir días de la semana a fechas específicas
    """
    Curso = apps.get_model('cursos', 'Curso')
    
    # Mapear días de la semana a números (lunes = 0, domingo = 6)
    dias_semana = {
        'lunes': 0, 'martes': 1, 'miércoles': 2, 'jueves': 3,
        'viernes': 4, 'sábado': 5, 'domingo': 6
    }
    
    # Obtener una fecha base (próximo lunes)
    hoy = timezone.now().date()
    dias_hasta_lunes = (7 - hoy.weekday()) % 7
    if dias_hasta_lunes == 0:
        dias_hasta_lunes = 7
    proximo_lunes = hoy + timedelta(days=dias_hasta_lunes)
    
    for curso in Curso.objects.all():
        dia_texto = curso.dia.lower()
        if dia_texto in dias_semana:
            # Calcular la fecha para ese día de la semana
            dia_numero = dias_semana[dia_texto]
            fecha_curso = proximo_lunes + timedelta(days=dia_numero)
            # Actualizar temporalmente en un campo auxiliar
            curso.dia_temp = fecha_curso
            curso.save()

def reverse_convert_date_to_day(apps, schema_editor):
    """Función inversa para revertir la migración si es necesario"""
    Curso = apps.get_model('cursos', 'Curso')
    
    dias_semana = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
    
    for curso in Curso.objects.all():
        if hasattr(curso, 'dia_temp') and curso.dia_temp:
            dia_semana = dias_semana[curso.dia_temp.weekday()]
            curso.dia = dia_semana.capitalize()
            curso.save()

class Migration(migrations.Migration):
    dependencies = [
        ('cursos', '0001_initial'),
    ]

    operations = [
        # Paso 1: Agregar campo temporal de fecha
        migrations.AddField(
            model_name='curso',
            name='dia_temp',
            field=models.DateField(null=True, blank=True),
        ),
        
        # Paso 2: Convertir datos existentes
        migrations.RunPython(convert_day_to_date, reverse_convert_date_to_day),
        
        # Paso 3: Eliminar campo dia original
        migrations.RemoveField(
            model_name='curso',
            name='dia',
        ),
        
        # Paso 4: Renombrar dia_temp a dia
        migrations.RenameField(
            model_name='curso',
            old_name='dia_temp',
            new_name='dia',
        ),
        
        # Paso 5: Hacer el campo obligatorio
        migrations.AlterField(
            model_name='curso',
            name='dia',
            field=models.DateField(help_text='Fecha específica del curso'),
        ),
    ]
