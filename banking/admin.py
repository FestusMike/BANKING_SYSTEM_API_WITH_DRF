from django.contrib import admin
from .models import Account, Transaction, Ledger


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "account_number",
        "user",
        "account_type",
        "current_balance",
        "date_created",
    )
    list_filter = ("account_type", "date_created")
    search_fields = ("account_number", "user__full_name", "user__email")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "from_account",
        "to_account",
        "transaction_type",
        "amount",
        "description",
        "timestamp",
    )
    list_filter = ("transaction_type", "timestamp")
    search_fields = (
        "transaction_id",
        "from_account__account_number",
        "to_account__account_number",
    )


@admin.register(Ledger)
class LedgerAdmin(admin.ModelAdmin):
    list_display = (
        "transaction",
        "account",
        "balance_after_transaction",
        
    )
    list_filter = ("account",)
    search_fields = ("transaction__transaction_id",)
