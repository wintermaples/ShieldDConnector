from wallet.models import *
import subprocess
from django.utils import timezone
import enum
from typing import Sequence
import json
import threading
from django.db.models import F
import time
from django.db import transaction

class Connector():

    def __init__(self, shieldd_path):
        self.shieldd_path = shieldd_path

    def create(self, id : str) -> Wallet:
        try:
            wallet = Wallet.objects.get(name=id)
        except Wallet.DoesNotExist:
            shieldd = subprocess.run((self.shieldd_path, 'getnewaddress'), stdout=subprocess.PIPE)
            address = shieldd.stdout.splitlines()[0].decode('utf-8')
            wallet = Wallet.objects.create(address=address, name=id, created_at=timezone.now())
        return wallet

    def get(self, id : str) -> Wallet:
        try:
            wallet = Wallet.objects.get(name=id)
        except Wallet.DoesNotExist:
            raise WalletNotFoundException()
        return wallet

    def delete(self, id: str) -> bool:
        try:
            wallet = Wallet.objects.get(name=id)
            wallet.delete()
            return True
        except Wallet.DoesNotExist:
            return False

    def list(self) -> Sequence[Wallet]:
        return Wallet.objects.all()

    def move(self, fromId: str, toId: str, amount: float, moveFeePercent: float) -> Transaction:
        try:
            amountReal = amount * (1 - moveFeePercent)
            fromWallet = Wallet.objects.get(name=fromId)
            toWallet = Wallet.objects.get(name=toId)

            if fromWallet.balance < amount:
                raise InsufficientFundsException()
            fromWallet.balance = F('balance') - amount
            toWallet.balance = F('balance') + amountReal

            txType, created = TransactionType.objects.get_or_create(name='Move')
            tx = Transaction(type=txType, fromAddrOrId=fromId, toAddrOrId=toId, amount=amountReal, fee=0, created_at=timezone.now())

            tx.save()
            fromWallet.save()
            toWallet.save()
            return tx
        except Wallet.DoesNotExist:
            raise WalletNotFoundException()

    def send(self, fromId: str, toAddr: str, amount: float, sendFeePercent: float) -> Transaction:
        if amount <= 0.05:
            raise AmountTooSmallException()

        try:
            fromWallet = Wallet.objects.get(name=fromId)
            if fromWallet.balance < amount:
                raise InsufficientFundsException()

            amountReal = amount * (1 - sendFeePercent)

            shieldd = subprocess.run((self.shieldd_path, 'sendfrom', "", toAddr, str(amountReal)), stdout=subprocess.PIPE)
            txId = shieldd.stdout.splitlines()[0]

            shieldd = subprocess.run((self.shieldd_path, 'gettransaction', txId), stdout=subprocess.PIPE)
            txData = json.loads(shieldd.stdout.decode('utf-8'))
            fee = abs(txData['fee'])

            fromWallet.balance = F('balance') - amount - fee

            txType, created = TransactionType.objects.get_or_create(name='Send')
            tx = Transaction(type=txType, fromAddrOrId=fromId, toAddrOrId=toAddr, amount=amountReal, fee=fee, created_at=timezone.now())

            tx.save()
            fromWallet.save()
            return tx
        except Wallet.DoesNotExist:
            raise WalletNotFoundException()

    def rain(self, fromId: str, toIds: Sequence[str], amount: float, rainFeePercent: float) -> Sequence[Transaction]:
        transaction.set_autocommit(False)
        txs = []
        toWallets = []
        try:
            amountReal = amount * (1 - rainFeePercent)
            fromWallet = Wallet.objects.get(name=fromId)

            for toId in toIds:
                toWallet = Wallet.objects.get(name=toId)

                if fromWallet.balance < amount:
                    raise InsufficientFundsException()
                toWallet.balance = F('balance') + amountReal

                txType, created = TransactionType.objects.get_or_create(name='Move')
                tx = Transaction(type=txType, fromAddrOrId=fromId, toAddrOrId=toId, amount=amountReal, fee=0, created_at=timezone.now())

                txs.append(tx)
                toWallets.append(toWallet)

            fromWallet.balance = F('balance') - amount * len(toIds)
            #保存処理
            for tx in txs:
                tx.save()
            for toWallet in toWallets:
                toWallet.save()
            fromWallet.save()
        except Wallet.DoesNotExist:
            transaction.rollback()
            raise WalletNotFoundException()
        finally:
            transaction.commit()
            transaction.set_autocommit(True)
        return txs


def receive():
    while True:
        time.sleep(60)
        shieldd = subprocess.run(('/home/wintermaples/SHIELDd', 'listreceivedbyaddress'), stdout=subprocess.PIPE)
        receives = json.loads(shieldd.stdout.decode('utf-8'))
        for receiveData in receives:
            try:
                w = Wallet.objects.get(address=receiveData['address'])
                w.balance = F('balance') + receiveData['amount'] - F('totalReceived')
                added = receiveData['amount'] - float(w.totalReceived)
                w.totalReceived = receiveData['amount']
                w.save()
                if added > 0:
                    print('Balance of Wallet of %s Added: %f' % (w.name, added))
                    txType, created = TransactionType.objects.get_or_create(name='Receive')
                    tx = Transaction(type=txType, fromAddrOrId=w.name, toAddrOrId=w.address, amount=added, fee=0, created_at=timezone.now())
                    tx.save()
            except Wallet.DoesNotExist:
                pass


receiveThread = threading.Thread(target=receive)
receiveThread.start()


class StatusData():
    def __init__(self, status_code, status_message):
        self.status_code = status_code
        self.status_message = status_message


class Status(enum.Enum):
    SUCCESS = StatusData('0', '')
    AUTH_FAILED = StatusData('G-0', '認証情報が間違っているマジ...')
    INTERNAL_ERROR = StatusData('G-1', '...システムがおかしいマジよ...Developerに報告してマジ...')
    INSUFFICIENT_ARGS = StatusData('G-2', '引数が足りないマジよ...')
    WALLET_NOT_FOUND = StatusData('G-3', 'ウォレットがまだ作られてないマジロ...')
    INSUFFICIENT_FUNDS = StatusData('G-4', '残高が足りないマジよ...')
    NEGATIVE_VALUE_SPECIFIED = StatusData('G-5', '負の値が入っているマジよ...')
    AMOUNT_TOO_SMALL = StatusData('G-6', '金額が小さすぎるマジロ...')

class WalletNotFoundException(Exception):
    pass


class InsufficientFundsException(Exception):
    pass

class AmountTooSmallException(Exception):
    pass