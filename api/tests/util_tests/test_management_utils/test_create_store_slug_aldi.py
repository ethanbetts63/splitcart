from django.test import TestCase
from api.utils.management_utils.create_store_slug_aldi import create_store_slug_aldi

class CreateStoreSlugAldiTest(TestCase):

    def test_basic_slug_creation(self):
        self.assertEqual(create_store_slug_aldi("Sydney"), "sydney")

    def test_slug_with_spaces(self):
        self.assertEqual(create_store_slug_aldi("Perth CBD"), "perth-cbd")

    def test_slug_with_special_characters(self):
        self.assertEqual(create_store_slug_aldi("St. Kilda (East)"), "st-kilda-east")

    def test_slug_with_leading_trailing_spaces(self):
        self.assertEqual(create_store_slug_aldi("  Brisbane  "), "brisbane")

    def test_slug_with_multiple_dashes(self):
        self.assertEqual(create_store_slug_aldi("North--Melbourne"), "north-melbourne")

    def test_empty_string(self):
        self.assertEqual(create_store_slug_aldi(""), "")

    def test_numeric_city_name(self):
        self.assertEqual(create_store_slug_aldi("City 123"), "city-123")
