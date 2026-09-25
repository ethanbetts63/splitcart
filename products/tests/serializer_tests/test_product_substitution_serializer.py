"""`ProductSubstitutionSerializer` -- what stands in for the product you asked for.

`ProductSubstitution` is symmetrical: one row means A and B substitute for each
other, and neither column is "the substitute". Which of the two a response
should describe therefore depends on which product the caller asked about, and
the serializer reads that from `original_product_id` in its context. Get it
wrong and the substitutes list offers the shopper the item they already have.
"""

import pytest

from products.serializers.product_substitution_serializer import (
    ProductSubstitutionSerializer,
)
from products.tests.factories import ProductFactory, ProductSubstitutionFactory


@pytest.mark.django_db
class TestWhichProductIsDescribed:
    def test_asking_about_a_gives_you_b(self):
        a = ProductFactory(name='Brand A Milk')
        b = ProductFactory(name='Brand B Milk')
        substitution = ProductSubstitutionFactory(product_a=a, product_b=b)

        data = ProductSubstitutionSerializer(
            substitution, context={'original_product_id': a.id}
        ).data

        assert data['id'] == b.id
        assert data['name'] == 'Brand B Milk'

    def test_asking_about_b_gives_you_a(self):
        """The same row, read from the other end."""
        a = ProductFactory(name='Brand A Milk')
        b = ProductFactory(name='Brand B Milk')
        substitution = ProductSubstitutionFactory(product_a=a, product_b=b)

        data = ProductSubstitutionSerializer(
            substitution, context={'original_product_id': b.id}
        ).data

        assert data['id'] == a.id
        assert data['name'] == 'Brand A Milk'


@pytest.mark.django_db
class TestTheMatchQuality:
    def test_the_level_is_reported_with_its_meaning(self):
        """`LVL1` means nothing to a shopper; the sentence behind it does."""
        substitution = ProductSubstitutionFactory(level='LVL1', score=0.9)

        data = ProductSubstitutionSerializer(
            substitution, context={'original_product_id': substitution.product_a.id}
        ).data

        assert data['level'] == 'LVL1'
        assert data['level_description'] == (
            'Same brand, same product, different size.'
        )

    def test_the_score_is_carried_through(self):
        substitution = ProductSubstitutionFactory(score=0.83)

        data = ProductSubstitutionSerializer(
            substitution, context={'original_product_id': substitution.product_a.id}
        ).data

        assert data['score'] == pytest.approx(0.83)

    def test_the_substitute_arrives_as_a_whole_product(self):
        """The substitutes screen renders prices and a picture from this, so it
        is the full product payload merged with the match quality, not a link."""
        substitution = ProductSubstitutionFactory()

        data = ProductSubstitutionSerializer(
            substitution, context={'original_product_id': substitution.product_a.id}
        ).data

        assert {'id', 'name', 'prices', 'image_url', 'slug'} <= set(data)
        assert {'level', 'level_description', 'score'} <= set(data)

    def test_a_list_of_substitutes_all_describe_the_other_side(self):
        original = ProductFactory(name='The one in the cart')
        first = ProductSubstitutionFactory(product_a=original)
        second = ProductSubstitutionFactory(product_b=original)

        data = ProductSubstitutionSerializer(
            [first, second], many=True, context={'original_product_id': original.id}
        ).data

        assert original.name not in [row['name'] for row in data]
