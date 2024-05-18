from django.db import models
from django.contrib.auth import get_user_model
from utils.tools import generate_transaction_id, generate_account_number, BaseModel
from .constants import ACCOUNT_TYPE, TRANSACTION_TYPE, TRANSACTION_MODE

# Create your models here.

User = get_user_model()

class Account(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accounts")
    account_number = models.BigIntegerField(
        unique=True, editable=False, default=generate_account_number
    )
    account_type = models.CharField(
        max_length=30, null=False, choices=ACCOUNT_TYPE, default="SAVINGS"
    )
    current_balance = models.DecimalField(max_digits=10, decimal_places=2)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Accounts"
        abstract = False
    
    def assign_account_number(self, *args, **kwargs):
        if self.user and not self.account_number:
            self.account_number = generate_account_number()
        super().save(*args, kwargs)

    def __str__(self) -> str:
        return f"{self.account_number} - {self.user.full_name}"

class Transaction(BaseModel):
    transaction_id = models.BigIntegerField(
        unique=True, editable=False, default=generate_transaction_id
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
    from_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name = "outgoing_transactions"
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name = "incoming_transactions"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Transactions"
        abstract = False
        
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = generate_transaction_id()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.transaction_id} - {self.from_account.user.full_name if self.transaction_type == 'DEBIT' else self.to_account.user.full_name}"

class Ledger(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    balance_after_transaction = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "Ledger"
        abstract = False
