from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from turnos.models import Turno

@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
@csrf_exempt
def cambiar_estado_turno_ajax(request):
    if request.method == 'POST':
        turno_id = request.POST.get('turno_id')
        nuevo_estado = request.POST.get('estado')
        if turno_id and nuevo_estado:
            turno = Turno.objects.filter(id=turno_id).first()
            if turno and turno.estado != nuevo_estado:
                turno.estado = nuevo_estado
                turno.save()
                return JsonResponse({'success': True, 'nuevo_estado': nuevo_estado})
            elif turno:
                return JsonResponse({'success': True, 'nuevo_estado': nuevo_estado})
        return JsonResponse({'success': False, 'error': 'Datos inválidos'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})
