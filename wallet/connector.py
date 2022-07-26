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
from decimal import *
import os


class Connector():
    instance = None

    def __init__(self, shieldd_path, interval_of_receiving=60, rpcuser='', rpcpassword=''):
        print('Connector Instance is created.')
        self.running = True
        self.shieldd_path = shieldd_path
        self.interval_of_receiving = interval_of_receiving
        self.rpcuser = rpcuser
        self.rpcpassword = rpcpassword
        Connector.instance = self

        # makemigrationsする時にスレッドが起動してしまうので環境変数でなんとかする
        if os.environ.get('SHIELDD_CONNECTOR_STOP') is None or os.environ.get('SHIELDD_CONNECTOR_STOP').lower() == "false":
            print('Receiving thread will be started...')
            self.receive_thread = threading.Thread(target=self.__receive)
            self.receive_thread.start()
            self.check_stop_signal_thread = threading.Thread(target=self.__check_stop_signal)
            self.check_stop_signal_thread.start()

    @transaction.atomic
    def create(self, system: WalletSystem, name: str) -> Wallet:
        if self.running is False:
            raise SystemAlreadyStoppedException()

        print(f"Created {name}'s wallet.")

        try:
            wallet = Wallet.objects.get(system=system, name=name)
        except Wallet.DoesNotExist:
            shieldd = subprocess.run(args=(self.shieldd_path, f'-rpcuser={self.rpcuser}', f'-rpcpassword={self.rpcpassword}', 'getnewaddress'), stdout=subprocess.PIPE)
            address = shieldd.stdout.decode('utf-8').splitlines()[0]
            wallet = Wallet.objects.create(system=system, address=address, name=name, created_at=timezone.now())
        return wallet

    @transaction.atomic
    def get(self, system: WalletSystem, name: str) -> Wallet:
        if self.running is False:
            raise SystemAlreadyStoppedException()

        try:
            wallet = Wallet.objects.get(system=system, name=name)
        except Wallet.DoesNotExist:
            raise WalletNotFoundException()
        return wallet

    @transaction.atomic
    def delete(self, system: WalletSystem, name: str) -> bool:
        if self.running is False:
            raise SystemAlreadyStoppedException()

        print(f"Deleted {name}'s wallet.")

        try:
            wallet = Wallet.objects.get(system=system, name=name)
            wallet.delete()
            return True
        except Wallet.DoesNotExist:
            return False

    @transaction.atomic
    def list(self, system: WalletSystem) -> Sequence[Wallet]:
        if self.running is False:
            raise SystemAlreadyStoppedException()

        return Wallet.objects.filter(system=system).all()

    @transaction.atomic
    def list_txs(self, system: WalletSystem, limit=1000, from_addr_or_name=None, to_addr_or_name=None,
                 created_at_start=None, created_at_end=None, txid=None) -> Sequence[Transaction]:
        # txidだけの場合は一意なのでそれで検索してすぐreturn
        if txid is not None:
            return list(Transaction.objects.filter(system=system, txid=txid))

        query = Transaction.objects.filter(system=system)

        if from_addr_or_name is not None:
            query = query.filter(from_addr_or_name=from_addr_or_name)
        if to_addr_or_name is not None:
            query = query.filter(to_addr_or_name=to_addr_or_name)
        if created_at_start is not None:
            query = query.filter(created_at__gte=created_at_start)
        if created_at_end is not None:
            query = query.filter(created_at__lte=created_at_end)

        result = list(query.all())

        if len(result) > limit:
            raise TooManyTxsException()

        return result

    @transaction.atomic
    def move(self, system: WalletSystem, from_name: str, to_name: str, amount: Decimal, move_fee_percent: Decimal) -> Transaction:
        if self.running is False:
            raise SystemAlreadyStoppedException()

        print(f'Moved {amount} from {system}.{from_name} to {system}.{to_name}. Fee%: {move_fee_percent}')

        try:
            amount_real = amount * (1 - move_fee_percent)
            from_wallet = Wallet.objects.get(system=system, name=from_name)
            to_wallet = Wallet.objects.get(system=system, name=to_name)

            if from_wallet.balance < amount:
                raise InsufficientFundsException()

            from_wallet.balance = F('balance') - amount
            to_wallet.balance = F('balance') + amount_real

            tx_type, created = TransactionType.objects.get_or_create(name='Move')
            tx = Transaction(system=system, type=tx_type, from_addr_or_name=from_name, to_addr_or_name=to_name, amount=amount_real,
                             fee=amount - amount_real, created_at=timezone.now())

            tx.save()
            from_wallet.save()
            to_wallet.save()
            return tx
        except Wallet.DoesNotExist:
            raise WalletNotFoundException()

    @transaction.atomic
    def send(self, system: WalletSystem, from_name: str, to_addr: str, amount: Decimal, send_fee_percent: Decimal) -> Transaction:
        if self.running is False:
            raise SystemAlreadyStoppedException()

        if amount <= 0.05:
            raise AmountTooSmallException()

        print(f'Sent {amount} from {system}.{from_name} to {system}.{to_addr}. Fee%: {send_fee_percent}')

        try:
            from_wallet = Wallet.objects.get(system=system, name=from_name)
            if from_wallet.balance < amount:
                raise InsufficientFundsException()

            amount_real = amount * (1 - send_fee_percent)
            amount_real = amount_real.quantize(Decimal('0.000001'), rounding=ROUND_DOWN)

            shieldd = subprocess.run(args=(self.shieldd_path, f'-rpcuser={self.rpcuser}', f'-rpcpassword={self.rpcpassword}', 'sendfrom', "", to_addr, str(amount_real)), stdout=subprocess.PIPE)
            txid = shieldd.stdout.decode('utf-8').splitlines()[0]

            shieldd = subprocess.run(args=(self.shieldd_path, f'-rpcuser={self.rpcuser}', f'-rpcpassword={self.rpcpassword}', 'gettransaction', txid), stdout=subprocess.PIPE)
            txData = json.loads(shieldd.stdout.decode('utf-8'))
            tx_fee = abs(txData['fee'])

            from_wallet.balance = F('balance') - amount - tx_fee

            tx_type, created = TransactionType.objects.get_or_create(name='Send')
            tx = Transaction(system=system, type=tx_type, from_addr_or_name=from_name, to_addr_or_name=to_addr, amount=amount_real,
                             txfee=tx_fee, fee=amount - amount_real, txid=txid, created_at=timezone.now())

            tx.save()
            from_wallet.save()
            return tx
        except Wallet.DoesNotExist:
            raise WalletNotFoundException()

    @transaction.atomic
    def rain(self, system: WalletSystem, from_name: str, to_names: Sequence[str], amount: Decimal, rain_fee_percent: Decimal) -> Transaction:
        if self.running is False:
            raise SystemAlreadyStoppedException()

        print(f'Rained {amount} by {system}.{from_name}. Fee%: {rain_fee_percent}')

        try:
            amount_real = amount * (1 - rain_fee_percent)
            from_wallet = Wallet.objects.get(system=system, name=from_name)
            to_wallets = Wallet.objects.filter(system=system, name__in=to_names)

            if from_wallet.balance < amount * len(to_wallets):
                raise InsufficientFundsException()

            from_wallet.balance = F('balance') - amount * len(to_names)
            to_wallets.update(balance=F('balance') + amount_real)

            tx_type, created = TransactionType.objects.get_or_create(name='Rain')
            tx = Transaction(system=system, type=tx_type, from_addr_or_name=from_name, amount=amount * len(to_names),
                             fee=amount * len(to_names) * rain_fee_percent, created_at=timezone.now())

            from_wallet.save()
            tx.save()
        except Wallet.DoesNotExist:
            raise WalletNotFoundException()
        return tx

    def __receive(self):
        try:
            shieldd = subprocess.run(args=(self.shieldd_path, f'-rpcuser={self.rpcuser}', f'-rpcpassword={self.rpcpassword}', 'listreceivedbyaddress'), stdout=subprocess.PIPE)
        except Exception as ex:
            import traceback
            shieldd = None
            print("Couldn't run SHIELDd.")
            traceback.print_exc()

        if shieldd is not None:
            print('Check receiving...')
            try:
                with transaction.atomic():
                    receives = json.loads(shieldd.stdout.decode('utf-8'))
                    for receiveData in receives:
                        try:
                            w = Wallet.objects.get(address=receiveData['address'])
                            w.balance = F('balance') + receiveData['amount'] - F('total_received')
                            added = receiveData['amount'] - float(w.total_received)
                            w.total_received = receiveData['amount']
                            w.save()
                            if added > 0:
                                print('Balance of Wallet of %s Added: %f' % (w.name, added))
                                txType, created = TransactionType.objects.get_or_create(name='Receive')
                                tx = Transaction(system=w.system, type=txType, from_addr_or_name=w.name, to_addr_or_name=w.address, amount=added,
                                                 fee=0,
                                                 created_at=timezone.now())
                                tx.save()
                        except Wallet.DoesNotExist:
                            pass
            except:
                import traceback
                traceback.print_exc()
                print('SHIELDd is not run. Trying after 60 seconds...')

        if self.running:
            self.receive_thread = threading.Timer(self.interval_of_receiving, self.__receive)
            self.receive_thread.start()


    # 環境変数 SHIELDD_CONNECTOR_STOP = Trueで停止
    def __check_stop_signal(self):
        if os.environ.get('SHIELDD_CONNECTOR_STOP') is not None and os.environ.get('SHIELDD_CONNECTOR_STOP').lower() is 'true':
            self.running = False
            print('===== SHIELDD WILL BE STOPPED =====')

        if self.running:
            self.receive_thread = threading.Timer(1, self.__check_stop_signal)
            self.receive_thread.start()


    def __run_shieldd(self, args):
        command = [self.shieldd_path]
        rpc_args = ['-rpcuser=bitcoinrpc', '-rpcpassword=E7xTVKPLdGj8ydb1uHKaEPALjHiTvpAwtkUuT3RmB9Sx']
        command.extend(rpc_args)
        return subprocess.run(args=command, stdout=subprocess.PIPE)

    @staticmethod
    def get_instance():
        if Connector.instance is None:
            Connector.instance = Connector('/home/shielddconnector/shield-cli', rpcuser='bitcoinrpc', rpcpassword='E7xTVKPLdGj8ydb1uHKaEPALjHiTvpAwtkUuT3RmB9Sx')
        return Connector.instance


class StatusData():
    def __init__(self, status_code, status_message):
        self.status_code = status_code
        self.status_message = status_message


class Status(enum.Enum):
    SUCCESS = StatusData('0', '')
    AUTH_FAILED = StatusData('G-0', '認証情報が間違っているマジ...')
    INTERNAL_ERROR = StatusData('G-1', '...システムがおかしいか、APIにわたす引数がおかしいマジよ...Developerに報告してマジ...')
    INSUFFICIENT_ARGS = StatusData('G-2', '引数が足りないマジよ...')
    WALLET_NOT_FOUND = StatusData('G-3', 'ウォレットがまだ作られてないマジロ...')
    INSUFFICIENT_FUNDS = StatusData('G-4', '残高が足りないマジよ...')
    NEGATIVE_VALUE_SPECIFIED = StatusData('G-5', '負の値が入っているマジよ...')
    AMOUNT_TOO_SMALL = StatusData('G-6', '金額が小さすぎるマジロ...')
    FORBIDDEN = StatusData('G-7', 'あなたにはその操作をする権限がありません!')
    SYSTEM_ALREADY_STOPPED = ('G-100', '既にウォレットシステムは停止状態に入っています!')
    TOO_MANY_TXS = ('G-8', 'トランザクションの検索結果が多すぎます!範囲を絞るか、limitを大きくしてください!')
    MANAGER_NOT_FOUND = ('G-9', '指定された名前の管理者は存在しません!')
    PERMISSION_NOT_FOUND = ('G-10', 'そのようなパーミッションは存在しません!')


class WalletNotFoundException(Exception):
    pass


class InsufficientFundsException(Exception):
    pass


class AmountTooSmallException(Exception):
    pass


class SystemAlreadyStoppedException(Exception):
    pass


class TooManyTxsException(Exception):
    pass


class PermissionNotFoundException(Exception):
    pass