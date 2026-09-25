"""The credential endpoints carry a credential-class throttle scope.

Before this, every auth endpoint fell through to a catch-all `anon: 5000/day` --
one password attempt every seventeen seconds, all day, against a site with no
account lockout. The scope is the whole control here, so a test that only
checked the setting would not notice the day a route stopped reaching the
scoped view.
"""

import pytest
from django.conf import settings
from django.urls import resolve, reverse

from users.views.auth_views import ThrottledLoginView, ThrottledRegisterView

LOGIN_RATE = settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['login']
LOGIN_ATTEMPTS_PER_MINUTE = int(LOGIN_RATE.split('/')[0])


class TestAuthRoutesReachTheScopedViews:
    def test_login_resolves_to_the_scoped_view(self):
        assert resolve(reverse('rest_login')).func.cls is ThrottledLoginView

    def test_registration_resolves_to_the_scoped_view(self):
        assert resolve(reverse('rest_register')).func.cls is ThrottledRegisterView

    def test_the_slashless_login_form_is_scoped_too(self):
        """dj_rest_auth routes `login/?$`, so `/api/auth/login` is a live URL."""
        assert resolve('/api/auth/login').func.cls is ThrottledLoginView

    def test_login_is_measured_in_attempts_per_minute(self):
        assert LOGIN_RATE.endswith('/minute')


@pytest.mark.django_db
class TestLoginThrottle:
    def test_repeated_failures_are_throttled(self, api_client, user):
        url = reverse('rest_login')
        payload = {'email': user.email, 'password': 'not-the-password'}

        for _ in range(LOGIN_ATTEMPTS_PER_MINUTE):
            response = api_client.post(url, payload, format='json')
            assert response.status_code == 400, response.content

        response = api_client.post(url, payload, format='json')
        assert response.status_code == 429
