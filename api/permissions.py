from rest_framework import permissions

class IsAuthenticatedOrAnonymous(permissions.BasePermission):
    """
    Allows access to authenticated users or anonymous users with an anonymous_id.
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to authenticated users or anonymous users with an anonymous_id.
        return request.user and request.user.is_authenticated or hasattr(request, 'anonymous_id')
