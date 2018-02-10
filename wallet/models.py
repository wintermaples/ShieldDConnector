from django.db import models

# Create your models here.

class Wallet(models.Model):
    address = models.CharField(max_length=35)
    name = models.CharField(max_length=100, unique=True, null=False)
    balance = models.DecimalField(default=0, null=False, max_digits=10+8, decimal_places=8)
    created_at = models.DateTimeField(null=False)
    totalReceived = models.DecimalField(default=0, null=False, max_digits=10+8, decimal_places=8)

    def __str__(self):
        return str(self.toDict())

    def toDict(self) -> dict:
        return {'address': str(self.address),
                'name': str(self.name),
                'balance': float(self.balance),
                'created_at': str(self.created_at),
                'totalReceived': float(self.totalReceived)}

class TransactionType(models.Model):
    name = models.CharField(max_length=16, null=False, unique=True)

class Transaction(models.Model):
    type = models.ForeignKey(TransactionType, on_delete=models.CASCADE)
    fromAddrOrId = models.CharField(max_length=100, null=False)
    toAddrOrId = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10+8, decimal_places=8, null=False)
    fee = models.DecimalField(max_digits=10+8, decimal_places=8, null=False)
    created_at = models.DateTimeField(null=False)

    def __str__(self):
        return str(self.toDict())

    def toDict(self) -> dict:
        return {'type': str(self.type.name),
                'fromAddrOrId': str(self.fromAddrOrId),
                'toAddrOrId': str(self.toAddrOrId),
                'amount': float(self.amount),
                'fee': float(self.fee),
                'created_at': str(self.created_at)}