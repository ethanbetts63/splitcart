from django.test import TestCase
from scraping.utils.product_scraping_utils.get_coles_categories import get_coles_categories

class GetColesCategoriesTest(TestCase):
    def test_get_coles_categories(self):
        expected_categories = [
            "meat-seafood", "fruit-vegetables", "dairy-eggs-fridge", "bakery",
            "deli", "pantry", "dietary-world-foods", "chips-chocolates-snacks",
            "drinks", "frozen", "household", "health-beauty", "baby", "pet", "liquorland",
        ]
        categories = get_coles_categories()
        self.assertEqual(categories, expected_categories)
