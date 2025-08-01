from django.test import TestCase
from django.db.utils import IntegrityError
from products.tests.test_helpers.model_factories import ProductFactory

class ProductModelTest(TestCase):

    def test_product_creation(self):
        product = ProductFactory()
        self.assertIsNotNone(product.id)
        self.assertIsNotNone(product.name)
        self.assertIsNotNone(product.brand)
        self.assertIsNotNone(product.size)

    def test_product_str_representation(self):
        product = ProductFactory(brand="TestBrand", name="TestProduct", size="100g")
        self.assertEqual(str(product), "TestBrand TestProduct (100g)")

    def test_unique_together_constraint(self):
        product_info = {
            "name": "UniqueProduct",
            "brand": "UniqueBrand",
            "size": "500g"
        }
        ProductFactory(**product_info)
        with self.assertRaises(IntegrityError):
            ProductFactory(**product_info)

    def test_substitute_goods_relationship(self):
        product1 = ProductFactory()
        product2 = ProductFactory()
        product3 = ProductFactory()

        product1.substitute_goods.add(product2, product3)
        self.assertEqual(product1.substitute_goods.count(), 2)
        self.assertIn(product2, product1.substitute_goods.all())
        self.assertIn(product3, product1.substitute_goods.all())

    def test_barcode_can_be_null(self):
        product = ProductFactory(barcode=None)
        self.assertIsNone(product.barcode)

    def test_category_relationship(self):
        product = ProductFactory()
        self.assertIsNotNone(product.category)
