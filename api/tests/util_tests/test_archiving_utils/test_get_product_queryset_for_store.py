
from django.test import TestCase
from django.db.models.query import QuerySet
from api.utils.archiving_utils.get_product_queryset_for_store import get_product_queryset_for_store
from companies.tests.test_helpers.model_factories import StoreFactory
from products.tests.test_helpers.model_factories import PriceFactory

class GetProductQuerysetForStoreTest(TestCase):
    def test_get_product_queryset_for_store(self):
        store = StoreFactory()
        price = PriceFactory(store=store)

        queryset = get_product_queryset_for_store(store)

        self.assertIsInstance(queryset, QuerySet)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), price)
