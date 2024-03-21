from django.db import models
from django.contrib.auth import get_user_model
from utils.tools import primary_key
from .constants import ACCOUNT_TYPE, TRANSACTION_TYPE, TRANSACTION_MODE

# Create your models here.

User = get_user_model()

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accounts")
    account_type = models.CharField(
        max_length=30, null=False, choices=ACCOUNT_TYPE, default="SAVINGS"
    )
    pin = models.CharField(max_length=250, null=True, blank=True)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2)
    date_created = models.DateTimeField(auto_now_add=True)


class Transaction(models.Model):
    transaction_id = models.BigIntegerField(
        unique=True, primary_key=True, editable=False, default=primary_key(15)
    )
    account = models.ForeignKey(
        Account, on_delete=models.DO_NOTHING, related_name="transactions"
    )
    transaction_type = models.CharField(
        max_length=20, choices=TRANSACTION_TYPE, null=False, default="DEBIT"
    )
    transaction_mode = models.CharField(
        max_length=50,
        choices=TRANSACTION_MODE,
        null=False,
        default="MOBILE APP TRANSFER",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    recipient_bank = models.CharField(max_length=50, null=False)
    recipient_number = models.CharField(max_length=10, null=False)
    recipient_name = models.CharField(max_length=50, null=False)
    description = models.CharField(max_length=255, null=True, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)

class Ledger(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, null=True, blank=True)
    debit_credit = models.CharField(max_length=10, choices=TRANSACTION_TYPE)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
