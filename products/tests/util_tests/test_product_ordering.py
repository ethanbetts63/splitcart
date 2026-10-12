"""The category filter in `get_bargain_first_ordering` names fields that exist.

Its first query runs against `ProductPriceSummary`, which reaches
`primary_category_slugs` only through `product`. It used to filter on the bare
name, which raised `FieldError` for every slug: every category carousel answered
500, and every category page swallowed the error and rendered an empty
carousel, in production, with nothing to say so.

The filter itself is a JSON `contains`, which SQLite cannot run, so these build
the querysets rather than evaluate them. Django resolves a filter's field names
when it is applied, which is exactly where the old one failed.
"""

from products.models import Product, ProductPriceSummary
from products.utils.product_ordering import _primary_category_slug_filter


def test_the_summary_query_reaches_the_slugs_through_product():
    ProductPriceSummary.objects.filter(
        _primary_category_slug_filter(['meat', 'seafood'], via='product__')
    )


def test_the_product_query_reads_its_own_field():
    Product.objects.filter(_primary_category_slug_filter(['meat']))
