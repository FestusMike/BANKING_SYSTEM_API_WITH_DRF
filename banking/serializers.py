from rest_framework import serializers
from .models import Transaction, Account


class TransferSerializer(serializers.Serializer):
    to_account_number = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    pin = serializers.CharField(max_length=4)

class AccountSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ["account_number", "user"]

    def get_user(self, obj):
        return obj.user.full_name

class TransactionSerializer(serializers.ModelSerializer):
    from_account = AccountSerializer()
    to_account = AccountSerializer()

    class Meta:
        model = Transaction
        fields = "__all__"