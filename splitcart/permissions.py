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
        # Read permissions (GET, HEAD, OPTIONS) are allowed regardless of authentication
        # or anonymous status. This allows public listing of data.
        if request.method in permissions.SAFE_METHODS:
            return True

        # For write permissions (POST, PUT, PATCH, DELETE), we require the user to
        # either be authenticated or have an anonymous ID.
        is_authenticated = request.user and request.user.is_authenticated
        is_anonymous_with_id = hasattr(request, 'anonymous_id') and request.anonymous_id is not None

        return is_authenticated or is_anonymous_with_id
