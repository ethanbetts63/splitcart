from rest_framework import permissions

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
