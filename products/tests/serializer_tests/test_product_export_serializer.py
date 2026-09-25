"""`ProductExportSerializer` -- the shape the local machine pulls down.

`/api/export/products/` is paged through by `manage.py generate --subs` before
it does any matching, so this is an internal contract between the server and the
local half of the pipeline. What it carries is deliberately narrow: identity and
the fields the matcher reasons over, and nothing that would make the export
heavier than the matcher needs.
"""

import pytest

from products.serializers.product_export_serializer import ProductExportSerializer
from products.tests.factories import ProductBrandFactory, ProductFactory


@pytest.mark.django_db
class TestProductExportSerializer:
    def test_it_carries_the_matching_key_and_the_identity(self):
        brand = ProductBrandFactory()
        product = ProductFactory(
            name='Full Cream Milk',
            brand=brand,
            normalized_name_brand_size='full-cream-milk-dairyco-2l',
            size='2L',
        )

        data = ProductExportSerializer(product).data

        assert data['id'] == product.id
        assert data['name'] == 'Full Cream Milk'
        assert data['normalized_name_brand_size'] == 'full-cream-milk-dairyco-2l'
        assert data['brand_id'] == brand.id
        assert data['size'] == '2L'

    def test_it_carries_the_size_and_category_lists(self):
        product = ProductFactory(
            sizes=['2L', '2 litre'], primary_category_slugs=['dairy-and-eggs']
        )

        data = ProductExportSerializer(product).data

        assert data['sizes'] == ['2L', '2 litre']
        assert data['primary_category_slugs'] == ['dairy-and-eggs']

    def test_a_product_with_no_brand_exports_a_null_brand_id(self):
        product = ProductFactory(brand=None)

        assert ProductExportSerializer(product).data['brand_id'] is None

    def test_it_carries_nothing_else(self):
        """The export is paged over the whole catalogue. Every field added here
        is paid for on every page, so the set is stated rather than inherited."""
        data = ProductExportSerializer(ProductFactory()).data

        assert set(data) == {
            'id',
            'name',
            'normalized_name_brand_size',
            'brand_id',
            'size',
            'sizes',
            'primary_category_slugs',
        }

    def test_many_products_serialise_as_a_list(self):
        ProductFactory()
        ProductFactory()

        from products.models import Product

        data = ProductExportSerializer(Product.objects.all(), many=True).data

        assert len(data) == 2
