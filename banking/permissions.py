from rest_framework import permissions
from .models import Transaction


class IsOwnerOfTransaction(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        user_accounts = user.accounts.all()

        if obj.from_account in user_accounts or obj.to_account in user_accounts:
            return True
        return False
