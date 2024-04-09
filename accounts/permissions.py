from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow only the owner of a profile or admin users to view and edit it.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        return obj == request.user
