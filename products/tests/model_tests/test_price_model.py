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

    def test_for_stores_returns_prices_at_requested_store(self, make_anchored_store):
        store = make_anchored_store()
        product = ProductFactory()
        price = PriceFactory(product=product, store=store)

        qs = Price.objects.for_stores([store.id])

        assert price in qs

    def test_for_stores_excludes_prices_at_other_stores(self, make_anchored_store):
        store_a = make_anchored_store()
        store_b = make_anchored_store()
        product = ProductFactory()
        price_a = PriceFactory(product=product, store=store_a)
        PriceFactory(product=product, store=store_b)

        qs = Price.objects.for_stores([store_a.id])

        assert price_a in qs
        assert qs.count() == 1

    def test_for_stores_empty_input_returns_empty_queryset(self):
        qs = Price.objects.for_stores([])
        assert qs.count() == 0
