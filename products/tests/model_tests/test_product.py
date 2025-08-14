from django.test import TestCase
from django.db.utils import IntegrityError
from products.tests.test_helpers.model_factories import ProductFactory
from companies.tests.test_helpers.model_factories import CategoryFactory

class ProductModelTest(TestCase):

    def test_product_creation(self):
        """Test that a product can be created with all fields."""
        product = ProductFactory()
        self.assertIsNotNone(product.id)
        self.assertIsNotNone(product.name)
        self.assertIsNotNone(product.brand)
        self.assertIsNotNone(product.size)
        self.assertIsNotNone(product.barcode)
        self.assertIsNotNone(product.image_url)
        self.assertIsNotNone(product.description)
        self.assertIsNotNone(product.country_of_origin)
        self.assertIsNotNone(product.allergens)
        self.assertIsNotNone(product.ingredients)

    def test_product_str_representation(self):
        """Test the string representation of the product."""
        product = ProductFactory(brand="TestBrand", name="TestProduct", size="100g")
        self.assertEqual(str(product), "TestBrand TestProduct (100g)")

    def test_unique_together_constraint(self):
        """Test the unique_together constraint on name, brand, and size."""
        product_info = {
            "name": "UniqueProduct",
            "brand": "UniqueBrand",
            "size": "500g"
        }
        ProductFactory(**product_info)
        with self.assertRaises(IntegrityError):
            ProductFactory(**product_info)

    def test_substitute_goods_relationship(self):
        """Test the many-to-many relationship for substitute goods."""
        product1 = ProductFactory()
        product2 = ProductFactory()
        product3 = ProductFactory()

        product1.substitute_goods.add(product2, product3)
        self.assertEqual(product1.substitute_goods.count(), 2)
        self.assertIn(product2, product1.substitute_goods.all())
        self.assertIn(product3, product1.substitute_goods.all())

    def test_category_relationship(self):
        """Test the many-to-many relationship with Category."""
        product = ProductFactory()
        category1 = CategoryFactory()
        category2 = CategoryFactory()

        product.category.add(category1, category2)
        self.assertEqual(product.category.count(), 2)
        self.assertIn(category1, product.category.all())
        self.assertIn(category2, product.category.all())

    def test_nullable_fields(self):
        """Test that fields that can be null are correctly handled."""
        product = ProductFactory(
            brand=None,
            size=None,
            barcode=None,
            image_url=None,
            description=None,
            country_of_origin=None,
            allergens=None,
            ingredients=None
        )
        self.assertIsNone(product.brand)
        self.assertIsNone(product.size)
        self.assertIsNone(product.barcode)
        self.assertIsNone(product.image_url)
        self.assertIsNone(product.description)
        self.assertIsNone(product.country_of_origin)
        self.assertIsNone(product.allergens)
        self.assertIsNone(product.ingredients)