from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class HasAPIKey(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get('Authorization')

        if not api_key:
            raise AuthenticationFailed('No API key provided')

        # Validate the API key here (e.g., check against a database or a hardcoded key)
        if api_key != 'your_valid_api_key':
            raise AuthenticationFailed('Invalid API key')

        # Return a user or None, depending on how you manage your users
        user = None  # Replace with logic to retrieve user based on the API key if needed
        return (user, None)  # Return a tuple of (user, auth)