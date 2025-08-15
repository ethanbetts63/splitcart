
from django.test import TestCase
from api.utils.archiving_utils.build_product_list import build_product_list, get_category_path
from companies.tests.test_helpers.model_factories import StoreFactory, CategoryFactory
from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory

class GetCategoryPathTest(TestCase):
    def test_get_category_path(self):
        parent_category = CategoryFactory(name='Parent')
        child_category = CategoryFactory(name='Child')
        child_category.parents.set([parent_category])
        grandchild_category = CategoryFactory(name='Grandchild')
        grandchild_category.parents.set([child_category])

        path = get_category_path(grandchild_category)
        self.assertEqual(path, ['Parent', 'Child', 'Grandchild'])

class BuildProductListTest(TestCase):
    def test_build_product_list(self):
        store = StoreFactory()
        category = CategoryFactory()
        product = ProductFactory()
        product.category.set([category])
        price = PriceFactory(store=store, product=product)

        product_list = list(build_product_list(store))

        self.assertEqual(len(product_list), 1)
        product_data = product_list[0]

        self.assertEqual(product_data['name'], product.name)
        self.assertEqual(product_data['brand'], product.brand)
        self.assertEqual(len(product_data['price_history']), 1)
        self.assertEqual(product_data['price_history'][0]['price'], str(price.price))
        self.assertEqual(product_data['category_paths'], [[category.name]])
