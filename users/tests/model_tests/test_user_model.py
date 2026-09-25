"""`User` -- an account is an email address.

`username` is removed from `AbstractUser` and `USERNAME_FIELD` is `email`, so
everything that normally leans on a username -- `create_user`, `createsuperuser`,
`authenticate` -- goes through `UserManager` instead. That is this project's
decision rather than Django's, which is why it is tested here.
"""

import pytest
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.db import IntegrityError, transaction

from users.tests.factories import TEST_PASSWORD, UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestAccountIdentity:
    def test_an_account_is_identified_by_its_email(self):
        assert User.USERNAME_FIELD == 'email'
        assert str(UserFactory(email='sam@example.com')) == 'sam@example.com'

    def test_there_is_no_username_column(self):
        """`AbstractUser.username` is set to `None`, which removes the field.

        The class attribute survives as `None`, so `hasattr` says yes and a
        query says no -- which is exactly the trap a caller filtering on
        `username=` falls into.
        """
        with pytest.raises(FieldDoesNotExist):
            User._meta.get_field('username')
        assert User().username is None

    def test_two_accounts_cannot_share_an_email(self):
        UserFactory(email='sam@example.com')

        with pytest.raises(IntegrityError), transaction.atomic():
            User.objects.create(email='sam@example.com')

    def test_an_account_can_sign_in_with_its_email(self):
        user = UserFactory(email='sam@example.com')

        assert authenticate(username='sam@example.com', password=TEST_PASSWORD) == user

    def test_the_wrong_password_authenticates_nobody(self):
        UserFactory(email='sam@example.com')

        assert authenticate(username='sam@example.com', password='wrong') is None


@pytest.mark.django_db
class TestUserManager:
    def test_creating_a_user_stores_a_hash_not_the_password(self):
        user = User.objects.create_user(email='sam@example.com', password='hunter2222')

        assert user.password != 'hunter2222'
        assert user.check_password('hunter2222')

    def test_the_email_domain_is_normalised(self):
        """`normalize_email` lowercases the domain, so one address is one account."""
        user = User.objects.create_user(email='Sam@EXAMPLE.com', password='hunter2222')

        assert user.email == 'Sam@example.com'

    def test_an_account_without_an_email_is_refused(self):
        with pytest.raises(ValueError):
            User.objects.create_user(email='', password='hunter2222')

    def test_a_superuser_is_staff_and_super(self):
        user = User.objects.create_superuser(
            email='root@example.com', password='hunter2222'
        )

        assert user.is_staff is True
        assert user.is_superuser is True

    def test_a_superuser_cannot_be_created_without_staff(self):
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                email='root@example.com', password='hunter2222', is_staff=False
            )

    def test_a_superuser_cannot_be_created_without_the_superuser_flag(self):
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                email='root@example.com', password='hunter2222', is_superuser=False
            )

    def test_an_ordinary_account_is_neither(self):
        user = User.objects.create_user(email='sam@example.com', password='hunter2222')

        assert user.is_staff is False
        assert user.is_superuser is False
