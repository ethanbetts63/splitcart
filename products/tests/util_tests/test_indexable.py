"""Which product pages are indexable, asked both ways the code asks it.

`indexable_products` feeds the sitemap and `is_indexable` decides a single
page's robots tag. Every case runs through both, so the sitemap can never list
a page that tells Google not to index it, or the other way round.
"""

from datetime import date, timedelta

import pytest

from companies.tests.factories import CompanyFactory
from products.models import Product
from products.tests.factories import PriceFactory, ProductFactory
from products.utils.indexable import indexable_products, is_indexable

TODAY = date(2026, 10, 14)
FRESH = TODAY - timedelta(days=3)


def stale(settings):
    return TODAY - timedelta(days=settings.INDEXABLE_PRICE_MAX_AGE_DAYS + 1)


def product_priced_at(*stores):
    """`stores` is (chain, scraped_date) pairs."""
    product = ProductFactory()
    for chain, scraped in stores:
        PriceFactory(product=product, company=CompanyFactory(name=chain), scraped_date=scraped)
    return product


def both_ways(product):
    in_sitemap = indexable_products(TODAY).filter(pk=product.pk).exists()
    loaded = Product.objects.prefetch_related('prices__company').get(pk=product.pk)
    on_page = is_indexable(loaded.prices.all(), TODAY)
    assert in_sitemap == on_page
    return on_page


@pytest.mark.django_db
class TestIndexable:
    def test_coles_and_woolworths_qualify(self):
        assert both_ways(product_priced_at(('Coles', FRESH), ('Woolworths', FRESH)))

    def test_aldi_beside_one_of_them_qualifies(self):
        assert both_ways(product_priced_at(('Aldi', FRESH), ('Woolworths', FRESH)))
        assert both_ways(product_priced_at(('Aldi', FRESH), ('Coles', FRESH)))

    def test_one_chain_does_not(self):
        assert not both_ways(product_priced_at(('Woolworths', FRESH)))

    def test_iga_is_not_a_second_chain(self):
        assert not both_ways(product_priced_at(('Iga', FRESH), ('Woolworths', FRESH)))

    def test_a_stale_price_does_not_count(self, settings):
        assert not both_ways(product_priced_at(('Coles', stale(settings)), ('Woolworths', FRESH)))

    def test_the_last_day_of_the_window_still_counts(self, settings):
        edge = TODAY - timedelta(days=settings.INDEXABLE_PRICE_MAX_AGE_DAYS)
        assert both_ways(product_priced_at(('Coles', edge), ('Woolworths', edge)))

    def test_a_third_stale_chain_does_not_rescue_a_single_fresh_one(self, settings):
        product = product_priced_at(
            ('Woolworths', FRESH), ('Coles', stale(settings)), ('Aldi', stale(settings))
        )
        assert not both_ways(product)
