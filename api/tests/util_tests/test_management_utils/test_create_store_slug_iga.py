from django.test import TestCase
from api.utils.management_utils.create_store_slug_iga import create_store_slug_iga

class CreateStoreSlugIgaTest(TestCase):

    def test_basic_slug_creation(self):
        self.assertEqual(create_store_slug_iga("IGA Cannington"), "cannington")

    def test_slug_with_fresh(self):
        self.assertEqual(create_store_slug_iga("IGA Fresh Perth"), "perth")

    def test_slug_with_spaces(self):
        self.assertEqual(create_store_slug_iga("IGA Xpress City"), "xpress-city")

    def test_slug_with_special_characters(self):
        self.assertEqual(create_store_slug_iga("IGA & Grocer's Delight!"), "grocers-delight")

    def test_slug_with_leading_trailing_spaces(self):
        self.assertEqual(create_store_slug_iga("  IGA  Suburb  "), "suburb")

    def test_empty_string(self):
        self.assertEqual(create_store_slug_iga(""), "")

    def test_only_iga_or_fresh(self):
        self.assertEqual(create_store_slug_iga("IGA Fresh"), "")

    def test_multiple_iga_fresh(self):
        self.assertEqual(create_store_slug_iga("IGA IGA Fresh Fresh Store"), "store")
