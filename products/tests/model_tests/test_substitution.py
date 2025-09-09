from django.test import TestCase
from products.models import ProductSubstitution
from products.tests.test_helpers.model_factories import ProductSubstitutionFactory, ProductFactory

class ProductSubstitutionModelTests(TestCase):

    def test_create_product_substitution(self):
        """Test that a ProductSubstitution object can be created successfully."""
        # 1. Arrange
        # The factory will create product_a and product_b automatically.
        sub_type = 'SIZE'
        sub_score = 0.95
        sub_source = 'test_source'

        # 2. Act
        self.assertEqual(ProductSubstitution.objects.count(), 0)
        substitution = ProductSubstitutionFactory(
            type=sub_type,
            score=sub_score,
            source=sub_source
        )

        # 3. Assert
        self.assertEqual(ProductSubstitution.objects.count(), 1)
        
        # Retrieve from DB to be sure
        db_sub = ProductSubstitution.objects.first()
        
        self.assertEqual(db_sub.type, sub_type)
        self.assertEqual(db_sub.score, sub_score)
        self.assertEqual(db_sub.source, sub_source)
        self.assertIsNotNone(db_sub.product_a)
        self.assertIsNotNone(db_sub.product_b)
