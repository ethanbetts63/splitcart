import pytest
from decimal import Decimal
from data_management.serializers.price_export_serializer import PriceExportSerializer
from products.tests.factories import PriceFactory


@pytest.mark.django_db
class TestPriceExportSerializer:
    def test_contains_expected_fields(self):
        price = PriceFactory()
        serializer = PriceExportSerializer(price)
        assert set(serializer.data.keys()) == {'id', 'product_id', 'store_id', 'price'}

    def test_product_id_field_value(self):
        price = PriceFactory()
        serializer = PriceExportSerializer(price)
        assert serializer.data['product_id'] == price.product_id

    def test_store_id_field_value(self):
        price = PriceFactory()
        serializer = PriceExportSerializer(price)
        assert serializer.data['store_id'] == price.store_id

    def test_price_field_value(self):
        price = PriceFactory(price=Decimal('3.49'))
        serializer = PriceExportSerializer(price)
        assert Decimal(serializer.data['price']) == Decimal('3.49')

    def test_id_field_value(self):
        price = PriceFactory()
        serializer = PriceExportSerializer(price)
        assert serializer.data['id'] == price.pk
