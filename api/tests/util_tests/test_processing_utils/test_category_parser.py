from django.test import TestCase
from api.utils.processing_utils.category_parser import (
    _parse_aldi_path,
    _parse_coles_path,
    _parse_iga_path,
    _parse_woolworths_path,
    get_category_path
)

class CategoryParserTest(TestCase):

    # --- Tests for _parse_aldi_path ---
    def test_parse_aldi_path_basic(self):
        product_data = {"categories": [{"name": "Dairy"}, {"name": "Milk"}]}
        path = _parse_aldi_path(product_data)
        self.assertEqual(path, ["Dairy", "Milk"])

    def test_parse_aldi_path_empty(self):
        product_data = {"categories": []}
        path = _parse_aldi_path(product_data)
        self.assertEqual(path, [])

    def test_parse_aldi_path_missing_name(self):
        product_data = {"categories": [{"id": "123"}]}
        path = _parse_aldi_path(product_data)
        self.assertEqual(path, [])

    # --- Tests for _parse_coles_path ---
    def test_parse_coles_path_basic(self):
        product_data = {
            "onlineHeirs": [
                {"subCategory": "Fresh", "category": "Fruit & Veg", "aisle": "Produce"}
            ]
        }
        path = _parse_coles_path(product_data)
        self.assertEqual(path, ["Fresh", "Fruit & Veg", "Produce"])

    def test_parse_coles_path_partial(self):
        product_data = {
            "onlineHeirs": [
                {"subCategory": "Fresh", "category": "Fruit & Veg"}
            ]
        }
        path = _parse_coles_path(product_data)
        self.assertEqual(path, ["Fresh", "Fruit & Veg"])

    def test_parse_coles_path_empty(self):
        product_data = {"onlineHeirs": []}
        path = _parse_coles_path(product_data)
        self.assertEqual(path, [])

    def test_parse_coles_path_missing_online_heirs(self):
        product_data = {"name": "Apple"}
        path = _parse_coles_path(product_data)
        self.assertEqual(path, [])

    # --- Tests for _parse_iga_path ---
    def test_parse_iga_path_basic(self):
        product_data = {
            "categories": [
                {"categoryBreadcrumb": "Bakery / Breads"}
            ]
        }
        path = _parse_iga_path(product_data)
        self.assertEqual(path, ["Bakery", "Breads"])

    def test_parse_iga_path_multiple_categories(self):
        product_data = {
            "categories": [
                {"categoryBreadcrumb": "Dairy / Milk"},
                {"categoryBreadcrumb": "Bakery / Breads"} # Should take the last one
            ]
        }
        path = _parse_iga_path(product_data)
        self.assertEqual(path, ["Bakery", "Breads"])

    def test_parse_iga_path_empty(self):
        product_data = {"categories": []}
        path = _parse_iga_path(product_data)
        self.assertEqual(path, [])

    def test_parse_iga_path_missing_breadcrumb(self):
        product_data = {"categories": [{"id": "123"}]}
        path = _parse_iga_path(product_data)
        self.assertEqual(path, [])

    # --- Tests for _parse_woolworths_path ---
    def test_parse_woolworths_path_basic(self):
        product_data = {
            "AdditionalAttributes": {
                "sapdepartmentname": "Fresh Food",
                "sapcategoryname": "Fruit & Vegetables",
                "sapsubcategoryname": "Apples",
                "sapsegmentname": "Red Apples"
            }
        }
        path = _parse_woolworths_path(product_data)
        self.assertEqual(path, ["Fresh Food", "Fruit & Vegetables", "Apples", "Red Apples"])

    def test_parse_woolworths_path_partial(self):
        product_data = {
            "AdditionalAttributes": {
                "sapdepartmentname": "Fresh Food",
                "sapcategoryname": "Fruit & Vegetables"
            }
        }
        path = _parse_woolworths_path(product_data)
        self.assertEqual(path, ["Fresh Food", "Fruit & Vegetables"])

    def test_parse_woolworths_path_category_slash(self):
        product_data = {
            "AdditionalAttributes": {
                "sapdepartmentname": "Pantry",
                "sapcategoryname": "Pasta / Sauces"
            }
        }
        path = _parse_woolworths_path(product_data)
        self.assertEqual(path, ["Pantry", "Pasta", "Sauces"])

    def test_parse_woolworths_path_empty(self):
        product_data = {"AdditionalAttributes": {}}
        path = _parse_woolworths_path(product_data)
        self.assertEqual(path, [])

    def test_parse_woolworths_path_missing_attributes(self):
        product_data = {"name": "Milk"}
        path = _parse_woolworths_path(product_data)
        self.assertEqual(path, [])

    # --- Tests for get_category_path router ---
    def test_get_category_path_router_aldi(self):
        product_data = {"categories": [{"name": "Dairy"}]}
        path = get_category_path(product_data, "aldi")
        self.assertEqual(path, ["Dairy"])

    def test_get_category_path_router_coles(self):
        product_data = {"onlineHeirs": [{"subCategory": "Fresh"}]}
        path = get_category_path(product_data, "coles")
        self.assertEqual(path, ["Fresh"])

    def test_get_category_path_router_iga(self):
        product_data = {"categories": [{"categoryBreadcrumb": "Bakery / Breads"}]}
        path = get_category_path(product_data, "iga")
        self.assertEqual(path, ["Bakery", "Breads"])

    def test_get_category_path_router_woolworths(self):
        product_data = {"AdditionalAttributes": {"sapdepartmentname": "Fresh Food"}}
        path = get_category_path(product_data, "woolworths")
        self.assertEqual(path, ["Fresh Food"])

    def test_get_category_path_router_unknown_company(self):
        product_data = {"some_key": "some_value"}
        path = get_category_path(product_data, "unknown_company")
        self.assertEqual(path, [])

    def test_get_category_path_router_case_insensitivity(self):
        product_data = {"categories": [{"name": "Dairy"}]}
        path = get_category_path(product_data, "ALDI")
        self.assertEqual(path, ["Dairy"])