from django.http import JsonResponse, HttpResponse
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import json
from .connector import *
from django.views.decorators.csrf import csrf_exempt
import traceback
from wallet.user_auth import check_permission
from django.views.decorators.http import require_POST
from django.db.models import ObjectDoesNotExist


@require_POST
@csrf_exempt
@check_permission(Permission.CREATE)
def create(request):
    system = WalletSystem.get_wallet_system_from_token(request.POST.get('token'))

    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        addr = str(Connector.get_instance().create(system, data['name']).address)
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
    system = WalletSystem.get_wallet_system_from_token(request.POST.get('token'))

    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        addr = str(Connector.get_instance().get(system, data['name']).address)
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
    system = WalletSystem.get_wallet_system_from_token(request.POST.get('token'))

    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        bal = float(Connector.get_instance().get(system, data['name']).balance)
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
    system = WalletSystem.get_wallet_system_from_token(request.POST.get('token'))

    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        success = Connector.get_instance().delete(system, data['name'])
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
    system = WalletSystem.get_wallet_system_from_token(request.POST.get('token'))

    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        wallets = [wallet.to_dict() for wallet in Connector.get_instance().list(system)]
        retData = wallets
        status = Status.SUCCESS
    except Exception as ex:
        status = Status.INTERNAL_ERROR
        print(ex)
    return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})


@require_POST
@csrf_exempt
@check_permission(Permission.LIST_TXS)
def list_txs(request):
    system = WalletSystem.get_wallet_system_from_token(request.POST.get('token'))

    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        limit = data.get('limit', 1000)
        from_addr_or_name = data.get('from_addr_or_name', None)
        to_addr_or_name = data.get('to_addr_or_name', None)
        created_at_start = data.get('created_at_start', None)
        created_at_end = data.get('created_at_end', None)
        txid = data.get('txid', None)
        txs = Connector.get_instance().list_txs(system, limit, from_addr_or_name, to_addr_or_name, created_at_start, created_at_end, txid)
        retData = json.dumps(txs)
        status = Status.SUCCESS
    except Exception as ex:
        status = Status.INTERNAL_ERROR
        print(ex)
    return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})


@require_POST
@csrf_exempt
@check_permission(Permission.MOVE)
def tip(request):
    system = WalletSystem.get_wallet_system_from_token(request.POST.get('token'))

    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        tx = Connector.get_instance().move(system, data['from'], data['to'], Decimal(data['amount']), Decimal(data['feePercent']))
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
    system = WalletSystem.get_wallet_system_from_token(request.POST.get('token'))

    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        tx = Connector.get_instance().send(system, data['from'], data['to'], Decimal(data['amount']), Decimal(data['feePercent']))
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
    system = WalletSystem.get_wallet_system_from_token(request.POST.get('token'))

    jsondata = request.POST['data'].replace("'", '"')
    data = json.loads(jsondata)
    retData = {}
    try:
        Connector.get_instance().rain(system, data['from'], data['to'], Decimal(data['amount']), Decimal(data['feePercent']))
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