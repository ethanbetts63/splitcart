"""The two doors into an account, and what each carries through.

Everything else about a session -- refresh, logout, the profile, password change
and reset -- is `freetheplatform.auth`'s and is routed as it comes in
`users/urls.py`. Login is the package's view with two things in front of it: the
body is bounded before anything is hashed, and the cart a signed-out browser
filled is handed to the account once the login has succeeded.

Registration is splitcart's own, because the package has none. It ends signed
in, the same way login does: cookies set, principal returned.
"""

import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.middleware.csrf import get_token
from freetheplatform.auth import LoginView as SharedLoginView
from freetheplatform.auth import set_auth_cookies
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.principal import principal
from users.serializers import LoginRequestSerializer, RegisterSerializer
from users.utils.session_merger import merge_anonymous_session

logger = logging.getLogger(__name__)


def _hand_over_the_cart(user, anonymous_id):
    """The merge never decides whether somebody is signed in.

    It runs in its own transaction, so a failure leaves both carts exactly as
    they were; the shopper is in either way, and can find the signed-out list
    again by signing out.
    """
    try:
        merge_anonymous_session(user, anonymous_id)
    except Exception:
        logger.exception("Anonymous cart merge failed for user id=%s.", user.pk)


class LoginView(SharedLoginView):
    def post(self, request, *args, **kwargs):
        body = LoginRequestSerializer(data=request.data)
        body.is_valid(raise_exception=True)

        response = super().post(request, *args, **kwargs)

        anonymous_id = body.validated_data.get("anonymous_id")
        if response.status_code == status.HTTP_200_OK and anonymous_id:
            user = get_user_model().objects.get(pk=response.data["id"])
            _hand_over_the_cart(user, anonymous_id)
        return response


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "register"

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = serializer.save()
        _hand_over_the_cart(user, serializer.validated_data.get("anonymous_id"))

        refresh = RefreshToken.for_user(user)
        # So the first write after signing up has a CSRF token to send back.
        get_token(request)
        response = Response(
            {**principal(user), "must_change_password": False}, status=status.HTTP_201_CREATED
        )
        set_auth_cookies(response, refresh.access_token, refresh)
        return response
