from django.test import TestCase
from api.utils.processing_utils.create_coles_url_slug import _create_coles_url_slug

class TestCreatecolesUrlSlug(TestCase):

    def test_create_coles_url_slug_with_valid_data(self):
        name = "Test Product"
        size = "1kg"
        slug = _create_coles_url_slug(name, size)
        self.assertEqual(slug, "test-product-1kg")

    def test_create_coles_url_slug_with_extra_spaces(self):
        name = "  Test  Product  "
        size = "  1kg  "
        slug = _create_coles_url_slug(name, size)
        self.assertEqual(slug, "test-product-1kg")

    def test_create_coles_url_slug_with_special_characters(self):
        name = "Test!@#$%^&*()_+-=[]{}\\|;:'\",./<>?`~Product"
        size = "1kg"
        slug = _create_coles_url_slug(name, size)
        self.assertEqual(slug, "test-product-1kg")

    def test_create_coles_url_slug_with_empty_data(self):
        name = ""
        size = ""
        slug = _create_coles_url_slug(name, size)
        self.assertEqual(slug, "")