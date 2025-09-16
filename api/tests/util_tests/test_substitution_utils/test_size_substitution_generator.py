from django.test import TestCase
from unittest.mock import Mock

from api.utils.substitution_utils.lvl2_substitution_generator import Lvl2SubstitutionGenerator
from products.models import Product, ProductBrand, ProductSubstitution
from products.tests.test_helpers.model_factories import ProductFactory, ProductBrandFactory

class Lvl2SubstitutionGeneratorTests(TestCase):

    def setUp(self):
        self.mock_command = Mock()
        self.mock_command.stdout.write = Mock()
        self.mock_command.style.SUCCESS = lambda x: x
        
        # Create a common brand for the test products
        self.brand = ProductBrandFactory(name='Arnott\'s')

    def test_generate_creates_substitution_for_similar_products(self):
        """Test that a substitution is created for products with similar names."""
        # 1. Arrange
        # These two products should be matched as size variants
        product_a = ProductFactory(
            brand=self.brand.canonical_name, 
            name='Arnott\'s Choc Ripple Biscuits 250g',
            normalized_name='arnotts choc ripple biscuits'
        )
        product_b = ProductFactory(
            brand=self.brand.canonical_name, 
            name='Choc Ripple Biscuits by Arnott\'s 200g',
            # token_set_ratio should handle the different word order
            normalized_name='choc ripple biscuits by arnotts' 
        )

        # This product should not be matched
        product_c = ProductFactory(
            brand=self.brand.canonical_name, 
            name='Arnott\'s Digestive Biscuits 300g',
            normalized_name='arnotts digestive biscuits'
        )

        generator = Lvl2SubstitutionGenerator(self.mock_command)

        # 2. Act
        self.assertEqual(ProductSubstitution.objects.count(), 0)
        generator.generate()

        # 3. Assert
        self.assertEqual(ProductSubstitution.objects.count(), 1)
        
        substitution = ProductSubstitution.objects.first()
        
        # Check that the substitution links the correct two products
        pair = {substitution.product_a, substitution.product_b}
        self.assertEqual(pair, {product_a, product_b})
        
        # Check the substitution details
        self.assertEqual(substitution.type, 'SIZE')
        self.assertEqual(substitution.score, 0.95)
        self.assertEqual(substitution.source, 'size_similarity_v1')
