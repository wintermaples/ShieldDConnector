from django.http import JsonResponse, HttpResponse
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import json
from .connector import *
from django.views.decorators.csrf import csrf_exempt
import traceback
from wallet.user_auth import check_permission
from django.views.decorators.http import require_POST
from django.db.models import ObjectDoesNotExist

connector = Connector('/home/wintermaples/SHIELDd')


@require_POST
@csrf_exempt
@check_permission(Permission.CREATE)
def create(request):
    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        addr = str(connector.create(data['id']).address)
        retData = addr
        status = Status.SUCCESS
    except Exception as ex:
        status = Status.INTERNAL_ERROR
        print(ex)
    return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})


@require_POST
@csrf_exempt
@check_permission(Permission.ADDRESS)
def address(request):
    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        addr = str(connector.get(data['id']).address)
        retData = addr
        status = Status.SUCCESS
    except WalletNotFoundException:
        status = Status.WALLET_NOT_FOUND
    except Exception as ex:
        status = Status.INTERNAL_ERROR
        print(ex)
    return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})


@require_POST
@csrf_exempt
@check_permission(Permission.BALANCE)
def balance(request):
    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        bal = float(connector.get(data['id']).balance)
        retData = bal
        status = Status.SUCCESS
    except WalletNotFoundException:
        status = Status.WALLET_NOT_FOUND
    except Exception as ex:
        status = Status.INTERNAL_ERROR
        print(ex)
    return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})


@require_POST
@csrf_exempt
@check_permission(Permission.DELETE)
def delete(request):
    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        success = connector.delete(data['id'])
        retData = success
        status = Status.SUCCESS
    except WalletNotFoundException:
        status = Status.WALLET_NOT_FOUND
    except Exception as ex:
        status = Status.INTERNAL_ERROR
        print(ex)
    return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})


@require_POST
@csrf_exempt
@check_permission(Permission.LIST)
def list(request):
    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        wallets = [wallet.to_dict() for wallet in connector.list()]
        retData = wallets
        status = Status.SUCCESS
    except Exception as ex:
        status = Status.INTERNAL_ERROR
        print(ex)
    return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})


@require_POST
@csrf_exempt
@check_permission(Permission.MOVE)
def tip(request):
    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        tx = connector.move(data['from'], data['to'], float(data['amount']), float(data['feePercent']))
        retData = tx.amount
        status = Status.SUCCESS
    except WalletNotFoundException:
        status = Status.WALLET_NOT_FOUND
    except InsufficientFundsException:
        status = Status.INSUFFICIENT_FUNDS
    except Exception as ex:
        status = Status.INTERNAL_ERROR
        print(traceback.format_exc())
    return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})


@require_POST
@csrf_exempt
@check_permission(Permission.SEND)
def send(request):
    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        tx = connector.send(data['from'], data['to'], float(data['amount']), float(data['feePercent']))
        retData = tx.amount
        status = Status.SUCCESS
    except WalletNotFoundException:
        status = Status.WALLET_NOT_FOUND
    except InsufficientFundsException:
        status = Status.INSUFFICIENT_FUNDS
    except AmountTooSmallException:
        status = Status.AMOUNT_TOO_SMALL
    except Exception as ex:
        status = Status.INTERNAL_ERROR
        print(ex)
    return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})


@require_POST
@csrf_exempt
@check_permission(Permission.RAIN)
def rain(request):
    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        connector.rain(data['from'], data['to'], float(data['amount']), float(data['feePercent']))
        status = Status.SUCCESS
    except WalletNotFoundException:
        status = Status.WALLET_NOT_FOUND
    except InsufficientFundsException:
        status = Status.INSUFFICIENT_FUNDS
    except AmountTooSmallException:
        status = Status.AMOUNT_TOO_SMALL
    except Exception as ex:
        status = Status.INTERNAL_ERROR
        print(ex)
    return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})


@require_POST
@csrf_exempt
@check_permission(Permission.ADD_MANAGER)
def add_manager(request):
    system = WalletSystem.get_wallet_system_from_token(request.POST.get('token'))

    jsondata = request.POST.get('data').replace("'", '"')
    data = json.loads(jsondata)
    retData = {}

    try:
        manager = ManagerFactory.create(system, data['name'], data['permissions'])
        retData['token'] = manager.token
        status = Status.SUCCESS
    except Exception as ex:
        status = Status.INTERNAL_ERROR
        print(ex)

    return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})


@require_POST
@csrf_exempt
@check_permission(Permission.REMOVE_MANAGER)
def remove_manager(request):
    system = WalletSystem.get_wallet_system_from_token(request.POST.get('token'))

    jsondata = request.POST.get('data').replace("'", '"')
    data = json.loads(jsondata)
    retData = {}

    try:
        manager = Manager.objects.get(system=system, name=data['name'])
        manager.delete()
        status = Status.SUCCESS
    except ObjectDoesNotExist:
        status = Status.MANAGER_NOT_FOUND
    except Exception as ex:
        status = Status.INTERNAL_ERROR
        print(ex)

    return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})


@require_POST
@csrf_exempt
@check_permission(Permission.MODIFY_PERMISSION)
def grant_permission(request):
    system = WalletSystem.get_wallet_system_from_token(request.POST.get('token'))

    jsondata = request.POST.get('data').replace("'", '"')
    data = json.loads(jsondata)
    retData = {}

    try:
        manager = Manager.objects.get(system=system, name=data['name'])
        permissions = manager.permissions
        try:
            permission = Permission.objects.get(name=data['permission'])
        except ObjectDoesNotExist:
            raise PermissionNotFoundException()

        permissions.add(permission)
        manager.save()
        status = Status.SUCCESS
    except ObjectDoesNotExist:
        status = Status.MANAGER_NOT_FOUND
    except PermissionNotFoundException:
        status = Status.PERMISSION_NOT_FOUND
    except Exception as ex:
        status = Status.INTERNAL_ERROR
        print(ex)

    return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})


@require_POST
@csrf_exempt
@check_permission(Permission.MODIFY_PERMISSION)
def deprive_permission(request):
    system = WalletSystem.get_wallet_system_from_token(request.POST.get('token'))

    jsondata = request.POST.get('data').replace("'", '"')
    data = json.loads(jsondata)
    retData = {}

    try:
        manager = Manager.objects.get(system=system, name=data['name'])
        permissions = manager.permissions
        try:
            permission = Permission.objects.get(name=data['permission'])
        except ObjectDoesNotExist:
            raise PermissionNotFoundException()

        permissions.remove(permission)
        manager.save()
        status = Status.SUCCESS
    except ObjectDoesNotExist:
        status = Status.MANAGER_NOT_FOUND
    except PermissionNotFoundException:
        status = Status.PERMISSION_NOT_FOUND
    except Exception as ex:
        status = Status.INTERNAL_ERROR
        print(ex)

    return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})


@require_POST
@csrf_exempt
@check_permission(Permission.GET_MANAGERS)
def get_managers(request):
    system = WalletSystem.get_wallet_system_from_token(request.POST.get('token'))

    jsondata = request.POST.get('data').replace("'", '"')
    data = json.loads(jsondata)
    retData = {}

    retData['managers'] = Manager.objects.filter(system=system).all()
    status = Status.SUCCESS

    return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})