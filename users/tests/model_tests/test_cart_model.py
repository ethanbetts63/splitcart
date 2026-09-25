"""`Cart` -- one active list per shopper, enforced twice.

Once in `save()`, which stands the previous one down, and once in the database,
which refuses two. Both matter: the `save()` half is what makes the ordinary
path work, and the constraint is what catches the paths that do not go through
it (`bulk_create`, a raw `update`, a future viewset action).
"""

import pytest
from django.db import IntegrityError, transaction

from users.models import Cart, CartItem
from users.tests.factories import CartFactory, CartItemFactory

ANONYMOUS_ID = 'e5f6a7b8-0000-4000-8000-000000000005'


@pytest.mark.django_db
class TestOnlyOneActiveCart:
    def test_activating_a_cart_stands_the_previous_one_down(self, user):
        first = CartFactory(user=user, is_active=True)

        CartFactory(user=user, is_active=True)

        first.refresh_from_db()
        assert first.is_active is False

    def test_a_second_active_cart_cannot_be_forced_in(self, user):
        """`bulk_create` does not call `save()`, so this is the constraint
        answering rather than the model's own bookkeeping."""
        CartFactory(user=user, is_active=True)

        with pytest.raises(IntegrityError), transaction.atomic():
            Cart.objects.bulk_create(
                [Cart(user=user, name='Sneaked in', is_active=True)]
            )

    def test_the_rule_is_per_account(self, user, other_user):
        mine = CartFactory(user=user, is_active=True)
        theirs = CartFactory(user=other_user, is_active=True)

        mine.refresh_from_db()
        theirs.refresh_from_db()
        assert mine.is_active is True
        assert theirs.is_active is True

    def test_the_rule_holds_for_anonymous_shoppers_too(self):
        first = CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)

        CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)

        first.refresh_from_db()
        assert first.is_active is False

    def test_two_anonymous_shoppers_may_each_have_one(self):
        mine = CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)
        theirs = CartFactory(
            user=None,
            anonymous_id='f6a7b8c9-0000-4000-8000-000000000006',
            is_active=True,
        )

        mine.refresh_from_db()
        theirs.refresh_from_db()
        assert mine.is_active is True
        assert theirs.is_active is True

    def test_inactive_carts_are_not_disturbed(self, user):
        kept = CartFactory(user=user, is_active=False, name='Last week')

        CartFactory(user=user, is_active=True)

        kept.refresh_from_db()
        assert kept.is_active is False

    def test_resaving_the_active_cart_does_not_deactivate_it(self, user):
        """The `exclude(pk=self.pk)` in `save()` is what makes a rename safe."""
        cart = CartFactory(user=user, is_active=True)

        cart.name = 'Renamed'
        cart.save()

        cart.refresh_from_db()
        assert cart.is_active is True


@pytest.mark.django_db
class TestCartNaming:
    def test_one_account_cannot_hold_two_carts_of_the_same_name(self, user):
        CartFactory(user=user, name='Weekly shop')

        with pytest.raises(IntegrityError), transaction.atomic():
            Cart.objects.create(user=user, name='Weekly shop')

    def test_two_accounts_may_each_use_the_same_name(self, user, other_user):
        CartFactory(user=user, name='Weekly shop')

        assert Cart.objects.create(user=other_user, name='Weekly shop').pk

    def test_a_cart_describes_itself_by_name_and_owner(self, user):
        cart = CartFactory(user=user, name='Weekly shop')

        assert str(cart) == f'Weekly shop ({user.email})'

    def test_an_ownerless_cart_says_so(self):
        cart = CartFactory(user=None, anonymous_id=ANONYMOUS_ID, name='Weekly shop')

        assert str(cart) == 'Weekly shop (Anonymous)'


@pytest.mark.django_db
class TestCartDeletion:
    def test_deleting_a_cart_takes_its_items_with_it(self, user):
        cart = CartFactory(user=user)
        CartItemFactory(cart=cart)
        CartItemFactory(cart=cart)

        cart.delete()

        assert CartItem.objects.count() == 0

    def test_deleting_an_account_takes_its_carts_with_it(self, user):
        CartFactory(user=user)

        user.delete()

        assert Cart.objects.count() == 0
