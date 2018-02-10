from django.http import JsonResponse, HttpResponse
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import json
from .connector import *
from django.views.decorators.csrf import csrf_exempt
import traceback

connector = Connector('/home/wintermaples/SHIELDd')

@csrf_exempt
def create(request):
    if request.method == 'POST':
        jsondata = request.POST['data'].replace("'", '"')
        data = json.loads(jsondata)
        retData = {}
        try:
            addr = connector.create(data['id'])
            retData = str(addr)
            status = Status.SUCCESS
        except Exception as ex:
            status = Status.INTERNAL_ERROR
            print(ex)
        return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})
    else:
        return HttpResponse(status=405)

@csrf_exempt
def address(request):
    if request.method == 'POST':
        jsondata = request.POST['data'].replace("'", '"')
        data = json.loads(jsondata)
        retData = {}
        try:
            addr = connector.address(data['id'])
            retData = str(addr)
            status = Status.SUCCESS
        except WalletNotFoundException:
            status = Status.WALLET_NOT_FOUND
        except Exception as ex:
            status = Status.INTERNAL_ERROR
            print(ex)
        return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})
    else:
        return HttpResponse(status=405)

@csrf_exempt
def balance(request):
    if request.method == 'POST':
        jsondata = request.POST['data'].replace("'", '"')
        data = json.loads(jsondata)
        retData = {}
        try:
            bal = connector.balance(data['id'])
            retData = bal
            status = Status.SUCCESS
        except WalletNotFoundException:
            status = Status.WALLET_NOT_FOUND
        except Exception as ex:
            status = Status.INTERNAL_ERROR
            print(ex)
        return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})
    else:
        return HttpResponse(status=405)

@csrf_exempt
def delete(request):
    if request.method == 'POST':
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
    else:
        return HttpResponse(status=405)

@csrf_exempt
def list(request):
    if request.method == 'POST':
        jsondata = request.POST['data'].replace("'", '"')
        data = json.loads(jsondata)
        retData = {}
        try:
            wallets = [wallet.toDict() for wallet in connector.list()]
            retData = wallets
            status = Status.SUCCESS
        except Exception as ex:
            status = Status.INTERNAL_ERROR
            print(ex)
        return JsonResponse({'result': retData, 'status': status.value.status_code, 'message': status.value.status_message})
    else:
        return HttpResponse(status=405)

@csrf_exempt
def tip(request):
    if request.method == 'POST':
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
    else:
        return HttpResponse(status=405)

@csrf_exempt
def send(request):
    if request.method == 'POST':
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
    else:
        return HttpResponse(status=405)

@csrf_exempt
def rain(request):
    if request.method == 'POST':
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
    else:
        return HttpResponse(status=405)