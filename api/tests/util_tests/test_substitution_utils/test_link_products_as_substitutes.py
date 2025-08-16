from django.test import TestCase
from products.tests.test_helpers.model_factories import ProductFactory
from api.utils.substitution_utils.link_products_as_substitutes import link_products_as_substitutes

class LinkProductsAsSubstitutesTest(TestCase):
    def setUp(self):
        self.product1 = ProductFactory()
        self.product2 = ProductFactory()
        self.product3 = ProductFactory()

    def test_link_products_as_substitutes(self):
        link_products_as_substitutes(self.product1, self.product2)

        # Check that product1 has product2 as a substitute
        self.assertIn(self.product2, self.product1.substitute_goods.all())
        # Check that product2 has product1 as a substitute (symmetrical)
        self.assertIn(self.product1, self.product2.substitute_goods.all())

        # Ensure no unintended links
        self.assertNotIn(self.product3, self.product1.substitute_goods.all())
        self.assertNotIn(self.product3, self.product2.substitute_goods.all())
