from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from .serializers import TransferSerializer
from .operations import transfer_funds

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
            transaction = transfer_funds(
                from_user,
                data["recipient_account_number"],
                data["amount"],
                data.get("description", ""),
            )
            return Response(
                {   "status" : status.HTTP_200_OK,
                    "Success" : True,
                    "message": f"Your transfer of {transaction.amount} to {transaction.recipient_account.user.full_name} is successful.",
                    "transaction_id": transaction.transaction_id,
                }
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
