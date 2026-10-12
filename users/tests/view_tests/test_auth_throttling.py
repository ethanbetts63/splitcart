"""The credential endpoints reach the views that carry their throttle.

Rate limiting here is a cost control; lockout, in the shared package, is the
credential control. The scope is still the whole of the cost control, so a test
that only checked the setting would not notice the day a route stopped reaching
the view that declares it.
"""

import pytest
from django.conf import settings
from django.urls import resolve, reverse

from users.views.auth_views import LoginView, RegisterView

LOGIN_RATE = settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['login']
LOGIN_ATTEMPTS_PER_MINUTE = int(LOGIN_RATE.split('/')[0])


class TestAuthRoutesReachTheScopedViews:
    def test_login_resolves_to_splitcarts_view(self):
        """Not the package's own: that one would skip the bound and the cart."""
        assert resolve(reverse('login')).func.cls is LoginView

    def test_registration_resolves_to_the_scoped_view(self):
        assert resolve(reverse('register')).func.cls is RegisterView
        assert RegisterView.throttle_scope == 'register'

    def test_login_is_measured_in_attempts_per_minute(self):
        assert LOGIN_RATE.endswith('/minute')


@pytest.mark.django_db
class TestLoginThrottle:
    def test_repeated_failures_are_throttled(self, api_client, user):
        url = reverse('login')
        payload = {'email': user.email, 'password': 'not-the-password'}

        for _ in range(LOGIN_ATTEMPTS_PER_MINUTE):
            response = api_client.post(url, payload, format='json')
            assert response.status_code == 401, response.content

        response = api_client.post(url, payload, format='json')
        assert response.status_code == 429
