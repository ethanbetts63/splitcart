"""Bounds on the registration serializer.

`/api/auth/registration/` is unauthenticated and hashes whatever it is given.
dj_rest_auth declares `password1`/`password2` as plain write-only `CharField`s
with no maximum and leaves `email` on DRF's unbounded `EmailField`, so before
these bounds existed a single request could hand the hasher a megabyte.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from users.models import Cart, CartItem
from users.tests.factories import CartFactory, CartItemFactory, UserFactory

from users.serializers.custom_register_serializer import (
    EMAIL_MAX_LENGTH,
    FULL_NAME_MAX_LENGTH,
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

    def test_full_name_at_the_limit_is_accepted(self):
        serializer = CustomRegisterSerializer(
            data=_payload(full_name='N' * FULL_NAME_MAX_LENGTH)
        )
        assert serializer.is_valid(), serializer.errors

    def test_full_name_over_the_limit_is_rejected(self):
        """The ceiling is the `name` kind, which is tighter than the 255-wide
        column -- FORMS-7 asks for the right kind, not a number that fits."""
        serializer = CustomRegisterSerializer(
            data=_payload(full_name='N' * (FULL_NAME_MAX_LENGTH + 1))
        )
        assert not serializer.is_valid()
        assert 'full_name' in serializer.errors

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


@pytest.mark.django_db
class TestRegistrationBehaviour:
    """What signing up does, beyond staying inside its bounds."""

    def test_a_new_account_is_created_and_signed_in(self, api_client):
        response = api_client.post(
            reverse('rest_register'), _payload(), format='json'
        )

        assert response.status_code == 201, response.content
        assert response.json()['key']

    def test_the_full_name_is_stored_on_the_account(self, api_client):
        """`full_name` is this project's addition to dj-rest-auth's serializer,
        and `save()` is the only thing that writes it."""
        api_client.post(
            reverse('rest_register'),
            _payload(full_name='Sam Rivers'),
            format='json',
        )

        assert (
            get_user_model().objects.get(email='new-person@example.com').full_name
            == 'Sam Rivers'
        )

    def test_an_email_already_in_use_is_rejected(self, api_client):
        UserFactory(email='new-person@example.com')

        response = api_client.post(
            reverse('rest_register'), _payload(), format='json'
        )

        assert response.status_code == 400
        assert 'email' in response.json()

    def test_mismatched_passwords_are_rejected(self, api_client):
        response = api_client.post(
            reverse('rest_register'),
            _payload(password2='something-else-entirely'),
            format='json',
        )

        assert response.status_code == 400
        assert not get_user_model().objects.filter(
            email='new-person@example.com'
        ).exists()

    def test_a_password_too_weak_for_the_validators_is_rejected(self, api_client):
        """`AUTH_PASSWORD_VALIDATORS` is configured; this proves registration
        actually runs them rather than only checking the length bound."""
        response = api_client.post(
            reverse('rest_register'),
            _payload(password1='password', password2='password'),
            format='json',
        )

        assert response.status_code == 400
        assert not get_user_model().objects.filter(
            email='new-person@example.com'
        ).exists()

    def test_the_stored_password_is_hashed(self, api_client):
        api_client.post(reverse('rest_register'), _payload(), format='json')

        user = get_user_model().objects.get(email='new-person@example.com')
        assert user.password != VALID_PASSWORD
        assert user.check_password(VALID_PASSWORD)

    def test_the_same_email_in_a_different_case_is_rejected(self, api_client):
        """MySQL's collation is case-insensitive, so `Sam@` and `sam@` are one
        row as far as the unique constraint is concerned."""
        UserFactory(email='new-person@example.com')

        response = api_client.post(
            reverse('rest_register'),
            _payload(email='NEW-PERSON@example.com'),
            format='json',
        )

        assert response.status_code == 400
        assert 'email' in response.json()

    def test_registering_twice_through_the_endpoint_is_a_400(self, api_client):
        """The path a person actually takes: sign up, forget, sign up again.

        The first registration leaves an unverified `EmailAddress` row, and
        dj-rest-auth's own uniqueness check only looks at verified ones -- which
        under `ACCOUNT_EMAIL_VERIFICATION = 'none'` is never any of them.
        """
        first = api_client.post(reverse('rest_register'), _payload(), format='json')
        assert first.status_code == 201, first.content

        second = api_client.post(reverse('rest_register'), _payload(), format='json')

        assert second.status_code == 400
        assert 'email' in second.json()
        assert get_user_model().objects.filter(
            email='new-person@example.com'
        ).count() == 1


ANONYMOUS_ID = 'c31b0e44-0000-4000-8000-000000000009'


@pytest.mark.django_db
class TestRegistrationAdoptsTheAnonymousCart:
    """Signing up used to lose the cart; signing in kept it.

    The merge lives in `users/utils/session_merger.py` and had exactly one
    caller: `CustomLoginSerializer.validate()`. Registration goes through
    dj-rest-auth's own serializer, which takes no `anonymous_id`, so a shopper
    who filled a cart signed out and then created an account lost it -- while
    the same shopper signing in kept it. `save()` now calls the same merger.
    """

    def test_the_signed_out_cart_follows_the_new_account(self, api_client):
        anon_cart = CartFactory(
            user=None, anonymous_id=ANONYMOUS_ID, is_active=True, name='Anonymous Cart'
        )
        item = CartItemFactory(cart=anon_cart, quantity=3)

        response = api_client.post(
            reverse('rest_register'),
            _payload(anonymous_id=ANONYMOUS_ID),
            format='json',
        )

        assert response.status_code == 201, response.content
        user = get_user_model().objects.get(email='new-person@example.com')
        merged = Cart.objects.get(user=user, is_active=True)
        assert [(i.product_id, i.quantity) for i in merged.items.all()] == [
            (item.product_id, 3)
        ]
        assert not Cart.objects.filter(pk=anon_cart.pk).exists()

    def test_registering_without_an_anonymous_id_creates_no_cart(self, api_client):
        CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)

        response = api_client.post(reverse('rest_register'), _payload(), format='json')

        assert response.status_code == 201, response.content
        user = get_user_model().objects.get(email='new-person@example.com')
        assert not Cart.objects.filter(user=user).exists()

    def test_an_unknown_anonymous_id_does_not_block_the_registration(self, api_client):
        response = api_client.post(
            reverse('rest_register'),
            _payload(anonymous_id=ANONYMOUS_ID),
            format='json',
        )

        assert response.status_code == 201, response.content

    def test_a_null_anonymous_id_is_accepted(self, api_client):
        """The frontend sends `null` when the browser has no stored ID."""
        response = api_client.post(
            reverse('rest_register'), _payload(anonymous_id=None), format='json'
        )

        assert response.status_code == 201, response.content

    def test_a_malformed_anonymous_id_is_a_400_not_a_500(self, api_client):
        """Declared as a `UUIDField` so the merger is never handed a raw string."""
        response = api_client.post(
            reverse('rest_register'),
            _payload(anonymous_id='not-a-uuid'),
            format='json',
        )

        assert response.status_code == 400
        assert 'anonymous_id' in response.json()

    def test_a_rejected_registration_does_not_hand_over_the_cart(self, api_client):
        """The merge happens in `save()`, which a failed validation never reaches."""
        anon_cart = CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)
        CartItemFactory(cart=anon_cart)

        response = api_client.post(
            reverse('rest_register'),
            _payload(anonymous_id=ANONYMOUS_ID, password2='something-else-entirely'),
            format='json',
        )

        assert response.status_code == 400
        anon_cart.refresh_from_db()
        assert anon_cart.is_active is True
        assert CartItem.objects.filter(cart=anon_cart).count() == 1
