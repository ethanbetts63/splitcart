"""The anonymous cart survives signing in.

Someone fills a cart while signed out, then creates an account or logs in. What
they put in the cart has to still be there afterwards. That is the whole of this
behaviour.

These tests exercise `merge_anonymous_session` directly rather than through an
endpoint, because the endpoints have been replaced once already -- dj-rest-auth's
serializers were the callers before `users/views/auth_views.py` -- and a test
written only against an endpoint is deleted along with it, taking the contract
with it.

The function has two callers, login and registration. That the two doors can
drift apart is the failure mode of this design, and
`view_tests/test_anonymous_cart_at_both_doors.py` drives both through the URL to
hold them together.
"""

import pytest

from users.models import Cart, CartItem
from users.tests.factories import (
    CartFactory,
    CartItemFactory,
    CartSubstitutionFactory,
    UserFactory,
)
from users.utils.session_merger import merge_anonymous_session

ANONYMOUS_ID = 'a2f1a7d0-0000-4000-8000-000000000001'


@pytest.mark.django_db
class TestAnonymousCartMerge:
    def test_anonymous_cart_items_become_the_users_active_cart(self, user):
        anon_cart = CartFactory(
            user=None, anonymous_id=ANONYMOUS_ID, is_active=True, name='Anonymous Cart'
        )
        item = CartItemFactory(cart=anon_cart, quantity=4)

        merge_anonymous_session(user, ANONYMOUS_ID)

        merged = Cart.objects.get(user=user, is_active=True)
        assert [(i.product_id, i.quantity) for i in merged.items.all()] == [
            (item.product_id, 4)
        ]

    def test_the_anonymous_cart_is_not_left_behind(self, user):
        anon_cart = CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)
        CartItemFactory(cart=anon_cart)

        merge_anonymous_session(user, ANONYMOUS_ID)

        assert not Cart.objects.filter(pk=anon_cart.pk).exists()
        assert not Cart.objects.filter(anonymous_id=ANONYMOUS_ID).exists()

    def test_no_cart_item_is_lost_in_the_move(self, user):
        anon_cart = CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)
        CartItemFactory(cart=anon_cart)
        CartItemFactory(cart=anon_cart)
        CartItemFactory(cart=anon_cart)

        merge_anonymous_session(user, ANONYMOUS_ID)

        assert CartItem.objects.count() == 3
        assert CartItem.objects.filter(cart__user=user).count() == 3

    def test_chosen_substitutes_move_with_their_item(self, user):
        """A substitute hangs off the cart item, so it has to survive the move.

        This is the half a re-parenting bug would lose silently: the item is
        still there, and only the approved substitute the shopper picked is gone.
        """
        anon_cart = CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)
        item = CartItemFactory(cart=anon_cart)
        substitution = CartSubstitutionFactory(original_cart_item=item, is_approved=True)

        merge_anonymous_session(user, ANONYMOUS_ID)

        merged_item = CartItem.objects.get(cart__user=user)
        assert list(merged_item.chosen_substitutions.values_list('id', flat=True)) == [
            substitution.id
        ]
        assert merged_item.chosen_substitutions.get().is_approved is True

    def test_the_users_own_active_cart_is_set_aside_not_deleted(self, user):
        """Two active carts would breach `unique_active_user_cart`.

        The signed-in cart is deactivated rather than removed: it is the
        shopper's own earlier list and nothing here has their permission to
        throw it away.
        """
        existing = CartFactory(user=user, is_active=True, name='Weekly shop')
        CartItemFactory(cart=existing)
        anon_cart = CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)
        CartItemFactory(cart=anon_cart)

        merge_anonymous_session(user, ANONYMOUS_ID)

        existing.refresh_from_db()
        assert existing.is_active is False
        assert existing.items.count() == 1
        assert Cart.objects.filter(user=user, is_active=True).count() == 1

    def test_an_empty_signed_out_cart_does_not_replace_the_accounts_own(self, user):
        """Signing out and straight back in arrives with the empty cart the
        signed-out visit was given. The account's list must survive it."""
        existing = CartFactory(user=user, is_active=True, name='Weekly shop')
        CartItemFactory(cart=existing)
        CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)

        merge_anonymous_session(user, ANONYMOUS_ID)

        existing.refresh_from_db()
        assert existing.is_active is True
        assert Cart.objects.filter(user=user, is_active=True).get() == existing

    def test_a_named_anonymous_cart_keeps_its_name(self, user):
        anon_cart = CartFactory(
            user=None, anonymous_id=ANONYMOUS_ID, is_active=True, name='Christmas lunch'
        )
        CartItemFactory(cart=anon_cart)

        merge_anonymous_session(user, ANONYMOUS_ID)

        assert Cart.objects.get(user=user, is_active=True).name == 'Christmas lunch'

    def test_the_default_anonymous_name_is_replaced(self, user):
        """"Anonymous Cart" is the placeholder the API invents, not a choice."""
        anon_cart = CartFactory(
            user=None, anonymous_id=ANONYMOUS_ID, is_active=True, name='Anonymous Cart'
        )
        CartItemFactory(cart=anon_cart)

        merge_anonymous_session(user, ANONYMOUS_ID)

        assert Cart.objects.get(user=user, is_active=True).name == 'Cart'

    def test_a_name_the_user_already_has_is_made_unique(self, user):
        """`unique_user_cart_name` is a database constraint; a clash is a 500."""
        CartFactory(user=user, name='Christmas lunch', is_active=False)
        anon_cart = CartFactory(
            user=None, anonymous_id=ANONYMOUS_ID, is_active=True, name='Christmas lunch'
        )
        CartItemFactory(cart=anon_cart)

        merge_anonymous_session(user, ANONYMOUS_ID)

        assert Cart.objects.get(user=user, is_active=True).name == 'Christmas lunch #1'

    def test_another_shoppers_anonymous_cart_is_untouched(self, user):
        """The ID is the only thing identifying a signed-out shopper."""
        theirs = CartFactory(
            user=None,
            anonymous_id='b9c4e5f2-0000-4000-8000-000000000002',
            is_active=True,
        )

        merge_anonymous_session(user, ANONYMOUS_ID)

        theirs.refresh_from_db()
        assert theirs.is_active is True
        assert theirs.user_id is None


@pytest.mark.django_db
class TestAnonymousCartMergeDoesNothing:
    """The no-op paths. Each of these used to be the difference between a login
    and a 500."""

    def test_an_unknown_anonymous_id_is_not_an_error(self, user):
        merge_anonymous_session(user, ANONYMOUS_ID)

        assert not Cart.objects.filter(user=user).exists()

    def test_an_inactive_anonymous_cart_is_not_claimed(self, user):
        """Only the cart the shopper is actually looking at moves across."""
        stale = CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=False)

        merge_anonymous_session(user, ANONYMOUS_ID)

        stale.refresh_from_db()
        assert stale.user_id is None
        assert not Cart.objects.filter(user=user).exists()

    def test_no_anonymous_id_means_nothing_happens(self, user):
        CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)

        merge_anonymous_session(user, None)

        assert not Cart.objects.filter(user=user).exists()

    def test_no_user_means_nothing_happens(self):
        anon_cart = CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)

        merge_anonymous_session(None, ANONYMOUS_ID)

        anon_cart.refresh_from_db()
        assert anon_cart.user_id is None
        assert anon_cart.is_active is True

    def test_merging_twice_does_not_duplicate_the_cart(self):
        """Idempotency: the second call has nothing left to find.

        A login retried after a dropped response must not leave the shopper with
        two copies of the same list.
        """
        user = UserFactory()
        anon_cart = CartFactory(user=None, anonymous_id=ANONYMOUS_ID, is_active=True)
        CartItemFactory(cart=anon_cart)

        merge_anonymous_session(user, ANONYMOUS_ID)
        merge_anonymous_session(user, ANONYMOUS_ID)

        assert Cart.objects.filter(user=user).count() == 1
        assert CartItem.objects.filter(cart__user=user).count() == 1


@pytest.mark.django_db
class TestAMergeThatCannotFinish:
    """The merge is four writes, and the first is destructive.

    In order: stand the user's own active cart down, create the replacement,
    move the items across, delete the anonymous cart. Without a transaction an
    interruption anywhere after step one left the shopper with no active cart
    and the list they had before switched off -- from their side, the cart
    vanished on sign-in.
    """

    def test_a_merge_that_cannot_finish_leaves_the_shopper_the_cart_they_had(
        self, user, monkeypatch
    ):
        theirs = CartFactory(user=user, name='Weekly shop', is_active=True)
        anon_cart = CartFactory(
            user=None, anonymous_id=ANONYMOUS_ID, is_active=True, name='Anonymous Cart'
        )
        CartItemFactory(cart=anon_cart)

        def fails(*args, **kwargs):
            raise RuntimeError('the database went away mid-merge')

        monkeypatch.setattr(Cart.objects, 'create', fails)

        with pytest.raises(RuntimeError):
            merge_anonymous_session(user, ANONYMOUS_ID)

        monkeypatch.undo()
        theirs.refresh_from_db()
        assert theirs.is_active is True
        assert Cart.objects.filter(user=user, is_active=True).count() == 1
