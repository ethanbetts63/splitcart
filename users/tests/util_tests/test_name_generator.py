"""`generate_unique_name` -- the thing standing between a default name and a 500.

`Cart` carries a database-level `unique_user_cart_name` constraint, so two carts
called "Shopping List" is an `IntegrityError`, not a duplicate row. Every place
that invents a name for someone goes through here first.
"""

import pytest

from users.models import Cart
from users.tests.factories import CartFactory
from users.utils.name_generator import generate_unique_name


@pytest.mark.django_db
class TestGenerateUniqueName:
    def test_an_unused_name_is_returned_unchanged(self, user):
        assert generate_unique_name(Cart, {'user': user}, 'Shopping List') == (
            'Shopping List'
        )

    def test_a_taken_name_gets_a_suffix(self, user):
        CartFactory(user=user, name='Shopping List')

        assert generate_unique_name(Cart, {'user': user}, 'Shopping List') == (
            'Shopping List #1'
        )

    def test_the_suffix_counts_up_past_the_ones_already_taken(self, user):
        CartFactory(user=user, name='Shopping List')
        CartFactory(user=user, name='Shopping List #1')
        CartFactory(user=user, name='Shopping List #2')

        assert generate_unique_name(Cart, {'user': user}, 'Shopping List') == (
            'Shopping List #3'
        )

    def test_a_gap_in_the_sequence_is_filled(self, user):
        """It looks for the first free name, not the highest one used."""
        CartFactory(user=user, name='Shopping List')
        CartFactory(user=user, name='Shopping List #2')

        assert generate_unique_name(Cart, {'user': user}, 'Shopping List') == (
            'Shopping List #1'
        )

    def test_another_owners_name_is_not_in_the_way(self, user, other_user):
        """The constraint is per owner, so two accounts may both have one."""
        CartFactory(user=other_user, name='Shopping List')

        assert generate_unique_name(Cart, {'user': user}, 'Shopping List') == (
            'Shopping List'
        )

    def test_the_owner_filter_may_be_an_anonymous_id(self):
        """Signed-out shoppers are identified by ID rather than by account."""
        anonymous_id = 'd4e5f6a7-0000-4000-8000-000000000004'
        CartFactory(user=None, anonymous_id=anonymous_id, name='Shopping List')

        assert generate_unique_name(
            Cart, {'anonymous_id': anonymous_id}, 'Shopping List'
        ) == 'Shopping List #1'
