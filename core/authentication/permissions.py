from rest_framework import permissions


class IsAdministrator(permissions.BasePermission):
    message = "You do not have the required permission to perform this action"
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return (user.is_staff and user.is_active and user.is_verified and 'admin' == user.role.lower()) or user.is_superuser
