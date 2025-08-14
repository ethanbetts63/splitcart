from django.test import TestCase
from api.utils.processing_utils.create_coles_url_slug import _create_coles_url_slug, create_coles_url_slug

class TestCreateColesUrlSlug(TestCase):

    # --- Tests for _create_coles_url_slug ---
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

    # --- Tests for create_coles_url_slug ---
    def test_create_coles_url_slug_main_function_valid_data(self):
        product_data = {"name": "Another Product", "size": "500g"}
        slug = create_coles_url_slug(product_data)
        self.assertEqual(slug, "another-product-500g")

    def test_create_coles_url_slug_main_function_missing_name(self):
        product_data = {"size": "500g"}
        slug = create_coles_url_slug(product_data)
        self.assertEqual(slug, "")

    def test_create_coles_url_slug_main_function_missing_size(self):
        product_data = {"name": "Another Product"}
        slug = create_coles_url_slug(product_data)
        self.assertEqual(slug, "")

    def test_create_coles_url_slug_main_function_empty_data(self):
        product_data = {"name": "", "size": ""}
        slug = create_coles_url_slug(product_data)
        self.assertEqual(slug, "")

    def test_create_coles_url_slug_main_function_none_data(self):
        product_data = {"name": None, "size": None}
        slug = create_coles_url_slug(product_data)
        self.assertEqual(slug, "")
