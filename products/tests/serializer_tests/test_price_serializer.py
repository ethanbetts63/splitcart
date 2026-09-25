"""`PriceSerializer` -- unreachable, and broken if it were reached.

It declares::

    price = serializers.DecimalField(source='price', ...)

and DRF asserts on exactly that: naming a `source` identical to the field name
raises `AssertionError: It is redundant to specify source='price'` the first
time the serializer's fields are bound. So any use of this class raises before
it serialises anything.

Nothing uses it. A repository-wide search for `PriceSerializer` finds only this
class and its own test; the cart and product payloads build their price lists in
`ProductSerializer.get_prices`, which is where the display rules live.

The recommendation is to delete the module. It is left in place because
`products/serializers/` is outside this plan's scope to remove from, and the
test below is the record: it asserts the behaviour a price serializer would owe
and is marked `xfail(strict=True)`, so it fails loudly the day the class is
repaired -- or passes out of existence with the file.
"""

from decimal import Decimal

import pytest

from companies.tests.factories import CompanyFactory
from products.serializers.price_serializer import PriceSerializer
from products.tests.factories import PriceFactory


@pytest.mark.django_db
@pytest.mark.xfail(
    strict=True,
    reason=(
        "PriceSerializer declares source='price' on a field named 'price', "
        "which DRF refuses. See this module's docstring."
    ),
)
def test_a_price_is_reported_with_its_supermarket():
    price = PriceFactory(
        company=CompanyFactory(name='Cheap Grocer'), price=Decimal('2.50')
    )

    data = PriceSerializer(price).data

    assert data == {'company': 'Cheap Grocer', 'price': '2.50'}
