
import unittest
from unittest.mock import Mock
from api.utils.normalization_utils.normalize_product_data import normalize_product_data

class TestNormalizeProductData(unittest.TestCase):

    def test_simple_product(self):
        # Mock product object
        product = Mock()
        product.name = "Test Product 1kg"
        product.brand = "TestBrand"
        product.sizes = []

        # Expected result:
        # name_sizes: ['1kg']
        # brand_sizes: []
        # existing_sizes: []
        # all_sizes: {'1kg'}
        # extracted_sizes: ['1kg']
        # cleaned_name: "Test Product"
        # normalized_string: "producttest" + "testbrand" + "1kg" = "producttesttestbrand1kg"
        expected_normalized_string = "producttesttestbrand1kg"

        normalized_string = normalize_product_data(product)
        self.assertEqual(normalized_string, expected_normalized_string)

    def test_product_with_brand_in_name(self):
        # Mock product object
        product = Mock()
        product.name = "TestBrand Awesome Product 250g"
        product.brand = "TestBrand"
        product.sizes = ["250g"]

        # Expected result:
        # name_sizes: ['250g']
        # brand_sizes: []
        # existing_sizes: ['250g']
        # all_sizes: {'250g'}
        # extracted_sizes: ['250g']
        # cleaned_name: "Awesome Product"
        # normalized_string: "awesomeproduct" + "testbrand" + "250g" = "awesomeproducttestbrand250g"
        expected_normalized_string = "awesomeproducttestbrand250g"

        normalized_string = normalize_product_data(product)
        self.assertEqual(normalized_string, expected_normalized_string)

    def test_product_with_multipack_size(self):
        # Test is failing because get_cleaned_name does not correctly remove the multipack string '6x' from the product name.
        # The function get_cleaned_name in api/utils/normalization_utils/get_cleaned_name.py might need a fix.
        # Mock product object
        product = Mock()
        product.name = "Juice Boxes 6x200ml"
        product.brand = "Juicy"
        product.sizes = []

        # Expected result:
        # name_sizes: ['6pk', '200ml']
        # brand_sizes: []
        # existing_sizes: []
        # all_sizes: {'6pk', '200ml'}
        # extracted_sizes: ['200ml', '6pk']
        # cleaned_name: "Juice Boxes"
        # normalized_string: "boxesjuice" + "juicy" + "200ml6pk" = "boxesjuicejuicy200ml6pk"
        expected_normalized_string = "boxesjuicejuicy200ml6pk"

        normalized_string = normalize_product_data(product)
        self.assertEqual(normalized_string, expected_normalized_string)

    def test_product_with_no_brand(self):
        # Mock product object
        product = Mock()
        product.name = "Generic Water Bottle 1.5L"
        product.brand = None
        product.sizes = []

        # Expected result:
        # name_sizes: ['1.5l']
        # brand_sizes: []
        # existing_sizes: []
        # all_sizes: {'1.5l'}
        # extracted_sizes: ['1.5l']
        # cleaned_name: "Generic Water Bottle"
        # normalized_string: "bottlegenericwater" + "" + "15l" = "bottlegenericwater15l"
        expected_normalized_string = "bottlegenericwater15l"

        normalized_string = normalize_product_data(product)
        self.assertEqual(normalized_string, expected_normalized_string)

    def test_product_with_existing_sizes(self):
        # Mock product object
        product = Mock()
        product.name = "Snack Bars"
        product.brand = "Yummy"
        product.sizes = ["5 pack", "150g"]

        # Expected result:
        # name_sizes: []
        # brand_sizes: []
        # existing_sizes: ['5 pack', '150g']
        # all_sizes: {'5 pack', '150g'} -> from extract_sizes: {'5pk', '150g'}
        # extracted_sizes: ['150g', '5pk']
        # cleaned_name: "Snack Bars"
        # normalized_string: "barssnack" + "yummy" + "150g5pk" = "barssnackyummy150g5pack"
        expected_normalized_string = "barssnackyummy150g5pack"

        normalized_string = normalize_product_data(product)
        self.assertEqual(normalized_string, expected_normalized_string)

if __name__ == '__main__':
    unittest.main()
