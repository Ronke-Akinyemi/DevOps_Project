from rest_framework import permissions, status
from business.models import Business
from rest_framework.exceptions import APIException

class IsUser(permissions.BasePermission):
    """
    Global permission check for authorized Users
    """
    message = "Only Users can perform this action"

    def has_permission(self,request,view):
        user = request.user

        if not user:
            return False

        return 'users' == user.role.lower()
            

class IsBusinessOwner(permissions.BasePermission):
    """
    Global permission check for Subscribers
    """
    message = "Only Business owners can do this"

    def has_permission(self, request, view):
        user = request.user
        if not user:
            return False
        return user.role == "OWNER"

class PaymentRequired(APIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "Your subscription is expired."
class IsSubscribed(permissions.BasePermission):
    """
    Global permission check for Subscribers
    """
    message = "Your subscription is expired."

    def has_permission(self, request, view):
        user = request.user

        # Check if the user is authenticated
        if not user.is_authenticated:
            return False

        # Check if the user is an OWNER
        if user.role == "OWNER":
            if not user.is_subscribed:
                raise PaymentRequired()
            return True

        # Check if the user is an ATTENDANT
        if user.role == "ATTENDANT":
            # Get the businesses the user is attending
            business = Business.objects.filter(attendants=user, is_active=True).first()
            if not business:
                return False
            
            if not business.owner.is_subscribed:
                raise PaymentRequired()
            return True
        return False

class IsAdministrator(permissions.BasePermission):
    message = "You do not have the required permission to perform this action"
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return (user.is_staff and user.is_active and user.is_verified and 'admin' == user.role.lower() and request.user.groups.filter(name='Administrator').exists()) or user.is_superuser

