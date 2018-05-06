from django.db import models
import uuid
from django.db.models import ObjectDoesNotExist


class WalletSystem(models.Model):
    name = models.CharField(max_length=32)
    token = models.CharField(max_length=32)

    def to_dict(self):
        return {
            'id': self.pk,
            'name': self.name
        }

    @staticmethod
    def get_wallet_system_from_token(token):
        system = None

        try:
            system = WalletSystem.objects.get(token=token)
        except ObjectDoesNotExist:
            pass

        try:
            manager = Manager.objects.get(token=token)
            system = manager.system
        except ObjectDoesNotExist:
            pass

        return system


class WalletSystemFactory:
    @staticmethod
    def create(name) -> WalletSystem:
        return WalletSystem(name=name, token=uuid.uuid4().hex)


class Manager(models.Model):
    system = models.ForeignKey(WalletSystem, on_delete=models.PROTECT)
    name = models.CharField(max_length=16)
    token = models.CharField(max_length=32)
    permissions = models.ManyToManyField('Permission')

    def to_dict(self):
        return {
            'id': self.pk,
            'system': self.system.to_dict(),
            'name': self.name,
            'permissions': [permission.to_dict() for permission in self.permissions.iterator()]
        }


class ManagerFactory:
    @staticmethod
    def create(system: WalletSystem, name, permissions):
        return Manager(system=system, name=name, token=uuid.uuid4().hex, permissions=permissions)


class Permission(models.Model):
    ADD_MANAGER = 'add_manager'
    REMOVE_MANAGER = 'remove_manager'
    MODIFY_PERMISSION = 'modify_permission'
    GET_MANAGERS = 'get_managers'
    BALANCE = 'balance'
    MOVE = 'move'
    SEND = 'send'
    RAIN = 'rain'
    ADDRESS = 'address'
    CREATE = 'create'
    DELETE = 'delete'
    LIST = 'list'
    LIST_TXS = 'list_txs'

    permissions = (ADD_MANAGER, REMOVE_MANAGER, MODIFY_PERMISSION, GET_MANAGERS,
                   BALANCE, MOVE, SEND, RAIN, ADDRESS, CREATE, DELETE, LIST, LIST_TXS)
    name = models.CharField(max_length=16)

    def to_dict(self):
        return {
            'id': self.pk,
            'name': self.name
        }


class Wallet(models.Model):
    system = models.ForeignKey(WalletSystem, db_index=True, on_delete=models.PROTECT)
    address = models.CharField(max_length=35, db_index=True)
    name = models.CharField(max_length=100, unique=True, null=False, db_index=True)
    balance = models.DecimalField(default=0, null=False, max_digits=10 + 8, decimal_places=8)
    created_at = models.DateTimeField(null=False)
    total_received = models.DecimalField(default=0, null=False, max_digits=10 + 8, decimal_places=8)

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self) -> dict:
        return {
            'address': str(self.address),
            'name': str(self.name),
            'balance': float(self.balance),
            'created_at': str(self.created_at),
            'total_received': float(self.total_received)
        }


class TransactionType(models.Model):
    name = models.CharField(max_length=16, null=False, unique=True)


class Transaction(models.Model):
    system = models.ForeignKey(WalletSystem, db_index=True, on_delete=models.PROTECT)
    type = models.ForeignKey(TransactionType, on_delete=models.PROTECT)
    from_addr_or_name = models.CharField(max_length=100, null=False, db_index=True)
    to_addr_or_name = models.CharField(max_length=100, db_index=True)
    amount = models.DecimalField(max_digits=10 + 8, decimal_places=8, null=False)
    txfee = models.DecimalField(max_digits=10 + 8, decimal_places=8, null=True)
    fee = models.DecimalField(max_digits=10 + 8, decimal_places=8, null=False)
    txid = models.CharField(max_length=64, null=True, db_index=True)
    created_at = models.DateTimeField(null=False, db_index=True)

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self) -> dict:
        return {
            'system': self.system.to_dict(),
            'type': str(self.type.name),
            'from_addr_or_name': str(self.from_addr_or_name),
            'to_addr_or_name': str(self.to_addr_or_name),
            'amount': self.amount,
            'txfee': self.txfee,
            'fee': self.fee,
            'txid': self.txid,
            'created_at': str(self.created_at)
        }
