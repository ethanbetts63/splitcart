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

class NoCacheApiMiddleware:
    """Gives an `/api/` response `no-store` unless it already decided otherwise.

    Section 7 of ../../freetheplatform/_docs/security-standard.md puts this in
    middleware rather than per view for one reason: per-view, the view somebody
    forgets is the one that leaks, and nothing about a missing header looks
    wrong.

    Unlike the same middleware in allbikes and bloomprint, this one defers to a
    response that already carries a `Cache-Control`. splitcart's API is mostly a
    public price catalogue, and six views carry `@cache_page` for two to
    twenty-four hours precisely because their answer does not depend on who is
    asking -- see config/tests/test_caching.py. An unconditional overwrite would
    delete that deliberate cache. The per-caller views -- auth, the cart
    viewset, the internal file exports -- carry `never_cache`, which emits
    `no-store` itself, so they are unaffected either way.

    What is left is the case the standard is actually about: a view that decided
    nothing. That one now says `no-store` instead of being cached by whatever
    sits in front of it while nobody is told.

    `private` as well as `no-store`, so a shared cache in front of the API
    cannot hold a response either.

    Scoped to `/api/` rather than every path, because the non-API surface here
    has nothing to protect and something to lose. The only production route
    outside `/api/` is the `/pillar-pages/` permanent redirect, which carries no
    caller's data and is deliberately cacheable forever; `/admin/` and
    `/static/` exist only under DEBUG, and the admin already wraps every view in
    `never_cache` of its own. A site-wide rule would buy nothing and make a 301
    uncacheable.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/api/") and not response.has_header("Cache-Control"):
            response["Cache-Control"] = "no-store, private"
        return response
