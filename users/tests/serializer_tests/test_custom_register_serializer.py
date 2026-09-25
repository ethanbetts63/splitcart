"""Bounds on the registration serializer.

`/api/auth/registration/` is unauthenticated and hashes whatever it is given.
dj_rest_auth declares `password1`/`password2` as plain write-only `CharField`s
with no maximum and leaves `email` on DRF's unbounded `EmailField`, so before
these bounds existed a single request could hand the hasher a megabyte.
"""

import pytest
from django.urls import reverse

from users.serializers.custom_register_serializer import (
    EMAIL_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    CustomRegisterSerializer,
)

VALID_PASSWORD = 'correct-horse-battery-7'


def _payload(**overrides):
    data = {
        'email': 'new-person@example.com',
        'full_name': 'New Person',
        'password1': VALID_PASSWORD,
        'password2': VALID_PASSWORD,
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
class TestCustomRegisterSerializerBounds:
    def test_password_at_the_limit_is_accepted(self):
        password = 'a7!' + 'x' * (PASSWORD_MAX_LENGTH - 3)
        assert len(password) == PASSWORD_MAX_LENGTH
        serializer = CustomRegisterSerializer(
            data=_payload(password1=password, password2=password)
        )
        assert serializer.is_valid(), serializer.errors

    def test_password_one_over_the_limit_is_rejected(self):
        password = 'a7!' + 'x' * (PASSWORD_MAX_LENGTH - 2)
        assert len(password) == PASSWORD_MAX_LENGTH + 1
        serializer = CustomRegisterSerializer(
            data=_payload(password1=password, password2=password)
        )
        assert not serializer.is_valid()
        assert 'password1' in serializer.errors

    def test_email_over_the_limit_is_rejected(self):
        local_part = 'e' * (EMAIL_MAX_LENGTH + 1 - len('@example.com'))
        email = f'{local_part}@example.com'
        assert len(email) == EMAIL_MAX_LENGTH + 1
        serializer = CustomRegisterSerializer(data=_payload(email=email))
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_full_name_is_still_required(self):
        data = _payload()
        del data['full_name']
        serializer = CustomRegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'full_name' in serializer.errors


@pytest.mark.django_db
class TestRegistrationEndpointBounds:
    """The bound has to hold at the boundary that first parses the request."""

    def test_over_long_password_is_rejected_by_the_endpoint(self, api_client):
        password = 'a7!' + 'x' * PASSWORD_MAX_LENGTH
        response = api_client.post(
            reverse('rest_register'),
            _payload(password1=password, password2=password),
            format='json',
        )
        assert response.status_code == 400
        assert 'password1' in response.json()

    def test_ordinary_registration_still_succeeds(self, api_client):
        response = api_client.post(
            reverse('rest_register'), _payload(), format='json'
        )
        assert response.status_code == 201, response.content
