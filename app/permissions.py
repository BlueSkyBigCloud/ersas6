from rest_framework.permissions import BasePermission
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

class CustomIsAuthenticated(BasePermission):
    """
    Custom permission that checks if a valid token is provided in the Authorization header.
    """

    def has_permission(self, request, view):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return False  # No token provided

        token = auth_header.split(' ')[1] if ' ' in auth_header else None

        if not token:
            return False  # Token is missing

        try:
            user, token = TokenAuthentication().authenticate_credentials(token)
        except AuthenticationFailed:
            return False  # Invalid token

        request.user = user
        return True