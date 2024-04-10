from rest_framework import serializers
from .models import Transaction, Ledger


class TransferSerializer(serializers.Serializer):
    to_account_number = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    pin = serializers.CharField(max_length=4)

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"

class LedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ledger
        fields = "__all__"
