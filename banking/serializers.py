from rest_framework import serializers


class TransferSerializer(serializers.Serializer):
    recipient_account_number = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    description = serializers.CharField(required=False)
    pin = serializers.CharField(max_length=4)
