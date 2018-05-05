import functools
from django.http.response import JsonResponse
from wallet.connector import Status
from wallet.models import *
from django.db.models import ObjectDoesNotExist


def check_permission(permission_type):
    def _check_permission(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            req = args[0]
            token = req.POST.get('token')
            if token is None:
                return JsonResponse({
                    'status': Status.FORBIDDEN.value.status_code, 'message': Status.FORBIDDEN.value.status_message
                })

            try:
                WalletSystem.objects.get(token=token)
            except ObjectDoesNotExist:
                pass
            else:
                return func(*args, **kwargs)

            try:
                manager = Manager.objects.get(token=token)
            except ObjectDoesNotExist:
                pass
            else:
                if any([permission.name == permission_type for permission in manager.permissions.iterator()]):
                    return func(*args, **kwargs)
                else:
                    return JsonResponse({
                        'status': Status.FORBIDDEN.value.status_code, 'message': Status.FORBIDDEN.value.status_message
                    })

            return JsonResponse({
                'status': Status.FORBIDDEN.value.status_code, 'message': Status.FORBIDDEN.value.status_message
            })

        return wrapper
    return _check_permission