import pytest
from decimal import Decimal
from products.models import Price
from products.tests.factories import ProductFactory, PriceFactory
from companies.tests.factories import StoreFactory


@pytest.mark.django_db
class TestPriceModel:
    def test_str_format(self):
        product = ProductFactory(name='Weet-Bix', brand=None, size=None)
        store = StoreFactory(store_name='Woolworths CBD')
        price = PriceFactory(product=product, store=store, price=Decimal('5.50'))
        assert 'Weet-Bix' in str(price)
        assert 'Woolworths CBD' in str(price)
        assert '5.50' in str(price)
