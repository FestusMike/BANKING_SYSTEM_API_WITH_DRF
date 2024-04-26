from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from .models import Account, Transaction, Ledger


def transfer_funds(from_account, to_account_number, amount, description):
    try:
        with transaction.atomic():
            from_account = Account.objects.select_for_update().get(user=from_account)
            if from_account.current_balance < amount:
                raise ValueError("Insufficient funds for transfer")

            to_account = Account.objects.select_for_update().get(
                account_number=to_account_number
            )

            debit_transaction = Transaction.objects.create(
                transaction_type="DEBIT",
                transaction_mode="MOBILE APP TRANSFER",
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                description=description,
            )

            from_account.current_balance -= amount
            from_account.save()
            Ledger.objects.create(
                account=from_account,
                transaction=debit_transaction,
                balance_after_transaction=from_account.current_balance,
            )

            credit_transaction = Transaction.objects.create(
                transaction_type="CREDIT",
                transaction_mode="MOBILE APP TRANSFER",
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                description=description,
            )

            to_account.current_balance += amount
            to_account.save()
            Ledger.objects.create(
                account=to_account,
                transaction=credit_transaction,
                balance_after_transaction=to_account.current_balance,
            )

    except ObjectDoesNotExist:
        raise ValueError("Recipient account doesn't exist")

    return debit_transaction, credit_transaction
