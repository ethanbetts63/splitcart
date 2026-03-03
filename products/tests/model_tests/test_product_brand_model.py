import pytest
from django.db import IntegrityError
from products.models import ProductBrand
from products.tests.factories import ProductBrandFactory


@pytest.mark.django_db
class TestProductBrandModel:
    def test_str_returns_name(self):
        brand = ProductBrandFactory(name='Sanitarium')
        assert str(brand) == 'Sanitarium'

    def test_normalized_name_uniqueness_enforced(self):
        ProductBrand.objects.create(name='Brand A', normalized_name='sanitarium')
        with pytest.raises(IntegrityError):
            ProductBrand.objects.create(name='Brand B', normalized_name='sanitarium')

    def test_name_variations_defaults_to_empty_list(self):
        brand = ProductBrandFactory()
        assert brand.name_variations == []

    def test_normalized_name_variations_defaults_to_empty_list(self):
        brand = ProductBrandFactory()
        assert brand.normalized_name_variations == []

    def test_confirmed_official_prefix_nullable(self):
        brand = ProductBrandFactory()
        assert brand.confirmed_official_prefix is None

    def test_longest_inferred_prefix_nullable(self):
        brand = ProductBrandFactory()
        assert brand.longest_inferred_prefix is None
