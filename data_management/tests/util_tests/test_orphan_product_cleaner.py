import pytest
from data_management.database_updating_classes.product_updating.post_processing.orphan_product_cleaner import OrphanProductCleaner
from products.models import Product
from products.tests.factories import ProductFactory, PriceFactory


@pytest.mark.django_db
class TestOrphanProductCleaner:
    def test_deletes_products_with_no_prices(self, mock_command):
        orphan = ProductFactory()
        cleaner = OrphanProductCleaner(mock_command)
        cleaner.run()
        assert not Product.objects.filter(pk=orphan.pk).exists()

    def test_preserves_products_with_prices(self, mock_command):
        price = PriceFactory()
        product = price.product
        cleaner = OrphanProductCleaner(mock_command)
        cleaner.run()
        assert Product.objects.filter(pk=product.pk).exists()

    def test_only_deletes_orphans_not_priced_products(self, mock_command):
        orphan = ProductFactory()
        price = PriceFactory()
        priced_product = price.product
        cleaner = OrphanProductCleaner(mock_command)
        cleaner.run()
        assert not Product.objects.filter(pk=orphan.pk).exists()
        assert Product.objects.filter(pk=priced_product.pk).exists()

    def test_no_orphans_does_not_delete_anything(self, mock_command):
        price = PriceFactory()
        product_count_before = Product.objects.count()
        cleaner = OrphanProductCleaner(mock_command)
        cleaner.run()
        assert Product.objects.count() == product_count_before

    def test_empty_database_runs_without_error(self, mock_command):
        cleaner = OrphanProductCleaner(mock_command)
        cleaner.run()  # Should not raise
