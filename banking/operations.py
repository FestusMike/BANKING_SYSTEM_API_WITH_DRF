from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from .models import Account, Transaction, Ledger


def transfer_funds(from_account, recipient_account_number, amount, description):
    try:
        with transaction.atomic():
            account = Account.objects.select_for_update().get(user=from_account)

            if account.current_balance < amount:
                raise ValueError("Insufficient funds for transfer")

            account.current_balance -= amount
            account.save()

            recipient_account = Account.objects.select_for_update().get(
                account_number=recipient_account_number
            )

            recipient_name = (
                recipient_account.user.full_name if recipient_account else "Unknown"
            )

            debit_transaction = Transaction.objects.create(
                account=account,
                transaction_type="DEBIT",
                amount=amount,
                recipient_account=recipient_account,
                description=f"Sent {amount} to {recipient_name}: {description}",
            )

            Ledger.objects.create(
                transaction=debit_transaction,
                amount=amount,
                debit_credit="DEBIT",
                description=f"Sent {amount} to {recipient_name}: {description}",
                balance=account.current_balance,
            )

            if recipient_account:
                recipient_account.current_balance += amount
                recipient_account.save()

                credit_transaction = Transaction.objects.create(
                    account=account,
                    transaction_type="CREDIT",
                    recipient_account=recipient_account,
                    amount=amount,
                    description=description,
                )

                Ledger.objects.create(
                    transaction=credit_transaction,
                    amount=amount,
                    debit_credit="CREDIT",
                    description=description,
                    balance=recipient_account.current_balance,
                )

    except ObjectDoesNotExist:
        raise ValueError("Recipient account doesn't exist")

    return debit_transaction
