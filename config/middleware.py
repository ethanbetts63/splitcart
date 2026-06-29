import uuid

class AnonymousUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # The frontend sends the ID in a header for its API calls.
        # For subsequent page loads or server-rendered pages, we rely on the cookie.
        anonymous_id = request.headers.get('X-Anonymous-ID') or request.COOKIES.get('anonymousId')

        new_id_generated = False
        if not anonymous_id:
            anonymous_id = str(uuid.uuid4())
            new_id_generated = True

        # Attach the determined ID to the request for use in views.
        request.anonymous_id = anonymous_id

        response = self.get_response(request)

        # If a new ID was created during this request, set it in the user's browser.
        if new_id_generated:
            max_age = 365 * 24 * 60 * 60  # One year
            response.set_cookie(
                'anonymousId',
                anonymous_id,
                max_age=max_age,
                # httponly=False allows JS to read it, but our new flow won't need this.
                # It's safer to keep it True if JS doesn't need to read it.
                # For now, let's assume the frontend might still benefit from reading it.
                httponly=False,
                samesite='Lax'
            )

        return response