"""Signing a test client in the way the browser is signed in.

A login sets two HttpOnly cookies and nothing else. Putting an access token in
the client's cookie jar is that state without a round trip through the login
view, whose own tests are in `view_tests/test_login.py`.
"""

from django.conf import settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

ACCESS_COOKIE = f"{settings.FTP_AUTH['COOKIE_PREFIX']}_access"
REFRESH_COOKIE = f"{settings.FTP_AUTH['COOKIE_PREFIX']}_refresh"


def sign_in(client, user):
    refresh = RefreshToken.for_user(user)
    client.cookies[ACCESS_COOKIE] = str(refresh.access_token)
    client.cookies[REFRESH_COOKIE] = str(refresh)
    return client


def client_for(user):
    return sign_in(APIClient(), user)
