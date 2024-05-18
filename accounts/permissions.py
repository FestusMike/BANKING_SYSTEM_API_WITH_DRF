from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow only the owner of a profile to view and edit it.
    """

    def has_object_permission(self, request, view, obj):
        return obj == request.user
