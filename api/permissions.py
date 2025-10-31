import os
from rest_framework import permissions

class IsInternalAPIRequest(permissions.BasePermission):
    """
    Allows access only to requests with a valid internal API key.
    """

    def has_permission(self, request, view):
        api_key = request.headers.get('X-Internal-API-Key')
        internal_api_key = os.environ.get('INTERNAL_API_KEY')
        if not internal_api_key:
            print("Server INTERNAL_API_KEY is not set.")
            return False
        
        is_authenticated = api_key == internal_api_key
        return is_authenticated

class IsAuthenticatedOrAnonymous(permissions.BasePermission):
    """
    Allows access to authenticated users or anonymous users with an anonymous_id.
    """

    def has_permission(self, request, view):
        # Allow POST requests to proceed, as the InitialSetupView handles session creation.
        if request.method == 'POST':
            return True

        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # For other methods like PUT, PATCH, DELETE, require authentication.
        return request.user and request.user.is_authenticated or hasattr(request, 'anonymous_id')
