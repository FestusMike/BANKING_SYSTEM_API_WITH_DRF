from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from .serializers import TransferSerializer, TransactionSerializer, LedgerSerializer
from .operations import transfer_funds
from .models import Transaction, Ledger
from .permissions import IsOwnerOfTransaction

User = get_user_model()


class TransferAPIView(generics.GenericAPIView):
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        from_user = request.user

        if not check_password(data["pin"], from_user.pin):
            return Response(
                {"error": "Incorrect PIN"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            debit_transaction, credit_transaction = transfer_funds(
                from_user.id,
                data["to_account_number"],
                data["amount"],
                data.get("description", ""),
            )

            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "Success": True,
                    "message": f"Your transfer of {debit_transaction.amount} to {credit_transaction.to_account.user.full_name} is successful.",
                    "transaction_id": debit_transaction.transaction_id,
                }
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserTransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOfTransaction]

    def get_queryset(self):
        user = self.request.user
        user_accounts = user.accounts.all()
        transactions = Transaction.objects.filter(
            from_account__in=user_accounts 
        ) | Transaction.objects.filter(
            to_account__in=user_accounts
         )
        return transactions.order_by('-timestamp')

class UserTransactionRetrieveView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOfTransaction]
    queryset = Transaction.objects.all()
    lookup_field = 'transaction_id'

    def get_object(self):
        transaction = super().get_object()
        user = self.request.user
        user_accounts = user.accounts.all()

        if transaction.from_account in user_accounts or transaction.to_account in user_accounts:
            return transaction
        else:
            raise generics.Http404


class StatementOfAccountAPIView(generics.ListAPIView):
    serializer_class = LedgerSerializer

    def get_queryset(self):
        user = self.request.user
        return Ledger.objects.filter(transaction__account__user=user)
