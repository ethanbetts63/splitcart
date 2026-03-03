import pytest
from django.db import IntegrityError
from products.models import Product
from products.tests.factories import ProductFactory, ProductBrandFactory


@pytest.mark.django_db
class TestProductModel:
    def test_str_with_brand_and_size(self):
        brand = ProductBrandFactory(name='Sanitarium')
        product = ProductFactory(name='Weet-Bix', brand=brand, size='750g')
        assert str(product) == 'Sanitarium Weet-Bix (750g)'

    def test_str_without_size(self):
        brand = ProductBrandFactory(name='Sanitarium')
        product = ProductFactory(name='Weet-Bix', brand=brand, size=None)
        assert str(product) == 'Sanitarium Weet-Bix'

    def test_normalized_name_brand_size_uniqueness_enforced(self):
        ProductFactory(normalized_name_brand_size='unique-key-abc')
        with pytest.raises(IntegrityError):
            Product.objects.create(name='Other', normalized_name_brand_size='unique-key-abc')

    def test_brand_name_company_pairs_defaults_to_empty_list(self):
        product = ProductFactory()
        assert product.brand_name_company_pairs == []

    def test_sizes_defaults_to_empty_list(self):
        product = ProductFactory()
        assert product.sizes == []
