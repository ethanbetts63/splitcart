from django.test import TestCase
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from products.models import Product
from products.tests.test_helpers.model_factories import ProductFactory, ProductBrandFactory
from companies.tests.test_helpers.model_factories import CategoryFactory

class ProductModelTest(TestCase):

    def test_product_creation(self):
        """Test that a product can be created with all fields."""
        product = ProductFactory(size="100g")
        self.assertIsNotNone(product.id)
        self.assertIsNotNone(product.name)
        self.assertTrue(len(product.sizes) > 0)

    def test_product_str_representation(self):
        """Test the string representation of the product."""
        brand = ProductBrandFactory(name="TestBrand")
        product = ProductFactory(brand=brand, name="TestProduct", size="100g, 200g")
        self.assertEqual(str(product), "TestBrand TestProduct (100g, 200g)")

    def test_product_str_representation_no_sizes(self):
        """Test the string representation of the product with no sizes."""
        brand = ProductBrandFactory(name="TestBrand")
        product = ProductFactory(brand=brand, name="TestProduct", size="")
        self.assertEqual(str(product), "TestBrand TestProduct ()")

    def test_normalized_name_brand_size_generation(self):
        """Test that normalized_name_brand_size is generated on save."""
        brand = ProductBrandFactory(name="Test Brand")
        product = ProductFactory(name="Test Product", brand=brand, size="100g")
        self.assertIsNotNone(product.normalized_name_brand_size)
        self.assertEqual(product.normalized_name_brand_size, "100gbrandproducttest")

    def test_unique_normalized_name_brand_size_constraint(self):
        """Test the unique constraint on normalized_name_brand_size."""
        brand = ProductBrandFactory(name="UniqueBrand")
        product_info = {
            "name": "UniqueProduct",
            "brand": brand,
            "size": "500g"
        }
        ProductFactory(**product_info)
        with self.assertRaises(IntegrityError):
            ProductFactory(**product_info)

    def test_unique_barcode_constraint(self):
        """Test the unique constraint on the barcode."""
        barcode = "1234567890123"
        ProductFactory(barcode=barcode)
        with self.assertRaises(IntegrityError):
            ProductFactory(barcode=barcode)

    def test_substitute_goods_relationship(self):
        """Test the many-to-many relationship for substitute goods."""
        product1 = ProductFactory()
        product2 = ProductFactory()
        product3 = ProductFactory()

        product1.substitutes.add(product2, product3, through_defaults={'score': 0.5})
        self.assertEqual(product1.substitutes.count(), 2)
        self.assertIn(product2, product1.substitutes.all())
        self.assertIn(product3, product1.substitutes.all())

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
            size="",
            barcode=None,
            image_url=None,
            url=None,
            description=None,
            country_of_origin=None,
            allergens=None,
            ingredients=None
        )
        self.assertIsNone(product.brand)
        self.assertEqual(product.sizes, [])
        self.assertIsNone(product.barcode)
        self.assertIsNone(product.image_url)
        self.assertIsNone(product.url)
        self.assertIsNone(product.description)
        self.assertIsNone(product.country_of_origin)
        self.assertIsNone(product.allergens)
        self.assertIsNone(product.ingredients)