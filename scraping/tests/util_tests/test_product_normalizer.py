import pytest
from scraping.utils.product_scraping_utils.product_normalizer import ProductNormalizer


class TestCleanValue:
    def test_lowercases_input(self):
        result = ProductNormalizer._clean_value('Hello World')
        assert result == 'hello world'

    def test_sorts_words_alphabetically(self):
        result = ProductNormalizer._clean_value('Banana Apple')
        assert result == 'apple banana'

    def test_deduplicates_words(self):
        result = ProductNormalizer._clean_value('Apple apple')
        assert result == 'apple'

    def test_removes_special_characters(self):
        result = ProductNormalizer._clean_value('Hello, World!')
        assert result == 'hello world'

    def test_unicode_normalization(self):
        result = ProductNormalizer._clean_value('café')
        assert result == 'cafe'

    def test_non_string_returns_empty(self):
        assert ProductNormalizer._clean_value(None) == ''
        assert ProductNormalizer._clean_value(123) == ''


class TestGetCleanedBarcode:
    def test_valid_ean13(self):
        normalizer = ProductNormalizer({'barcode': '1234567890123'})
        assert normalizer.get_cleaned_barcode() == '1234567890123'

    def test_12_digit_padded_to_13(self):
        normalizer = ProductNormalizer({'barcode': '123456789012'})
        assert normalizer.get_cleaned_barcode() == '0123456789012'

    def test_notfound_string_returns_none(self):
        normalizer = ProductNormalizer({'barcode': 'notfound'})
        assert normalizer.get_cleaned_barcode() is None

    def test_null_string_returns_none(self):
        normalizer = ProductNormalizer({'barcode': 'null'})
        assert normalizer.get_cleaned_barcode() is None

    def test_none_barcode_returns_none(self):
        normalizer = ProductNormalizer({'barcode': None})
        assert normalizer.get_cleaned_barcode() is None

    def test_short_barcode_returns_none(self):
        normalizer = ProductNormalizer({'barcode': '12345'})
        assert normalizer.get_cleaned_barcode() is None

    def test_prefers_ean13_over_12_digit(self):
        normalizer = ProductNormalizer({'barcode': '123456789012,1234567890123'})
        assert normalizer.get_cleaned_barcode() == '1234567890123'


class TestSizeExtraction:
    def test_simple_grams_from_name(self):
        normalizer = ProductNormalizer({'name': 'Milk 500g', 'brand': '', 'size': ''})
        assert '500g' in normalizer.raw_sizes

    def test_multipack_from_name(self):
        normalizer = ProductNormalizer({'name': '6 x 375ml', 'brand': '', 'size': ''})
        assert '375ml' in normalizer.raw_sizes
        assert '6pk' in normalizer.raw_sizes

    def test_size_from_size_field(self):
        normalizer = ProductNormalizer({'name': 'Milk', 'brand': '', 'size': '2L'})
        assert '2l' in normalizer.raw_sizes

    def test_no_size_returns_empty(self):
        normalizer = ProductNormalizer({'name': 'Unknown Product', 'brand': '', 'size': ''})
        assert normalizer.raw_sizes == []

    def test_kg_size(self):
        normalizer = ProductNormalizer({'name': 'Chicken 1.5kg', 'brand': '', 'size': ''})
        assert '1.5kg' in normalizer.raw_sizes

    def test_range_pattern(self):
        normalizer = ProductNormalizer({'name': '100-200g product', 'brand': '', 'size': ''})
        assert '100g' in normalizer.raw_sizes
        assert '200g' in normalizer.raw_sizes


class TestStandardizedSizes:
    def test_kg_converted_to_canonical(self):
        normalizer = ProductNormalizer({'name': 'Product 1kg', 'brand': '', 'size': ''})
        assert '1000g' in normalizer.standardized_sizes

    def test_litre_converted_to_canonical(self):
        normalizer = ProductNormalizer({'name': 'Drink 1l', 'brand': '', 'size': ''})
        assert '1000ml' in normalizer.standardized_sizes

    def test_1ea_simplified_to_ea(self):
        normalizer = ProductNormalizer({'name': '', 'brand': '', 'size': '1each'})
        assert 'ea' in normalizer.standardized_sizes


class TestGetNormalizedBrandName:
    def test_brand_is_normalized(self):
        normalizer = ProductNormalizer({'brand': 'Coca Cola'})
        assert normalizer.get_normalized_brand_name() == 'coca cola'

    def test_brand_is_translated(self):
        normalizer = ProductNormalizer(
            {'brand': 'CC'},
            brand_translations={'cc': 'coca cola'}
        )
        assert normalizer.get_normalized_brand_name() == 'coca cola'

    def test_empty_brand_returns_empty(self):
        normalizer = ProductNormalizer({'brand': ''})
        assert normalizer.get_normalized_brand_name() == ''

    def test_none_brand_returns_empty(self):
        normalizer = ProductNormalizer({'brand': None})
        assert normalizer.get_normalized_brand_name() == ''


class TestGetNormalizedNameBrandSizeString:
    def test_contains_words_from_name(self):
        normalizer = ProductNormalizer({'name': 'Full Cream Milk', 'brand': '', 'size': ''})
        result = normalizer.get_normalized_name_brand_size_string()
        assert 'cream' in result
        assert 'milk' in result

    def test_contains_size_in_standardized_form(self):
        normalizer = ProductNormalizer({'name': 'Milk', 'brand': '', 'size': '2L'})
        result = normalizer.get_normalized_name_brand_size_string()
        assert '2000ml' in result

    def test_product_translation_applied(self):
        # The generated key for 'Whole Milk' with no brand and 2L size
        normalizer = ProductNormalizer(
            {'name': 'Whole Milk', 'brand': '', 'size': ''},
            product_translations={'milk whole': 'canonical-key-abc'}
        )
        result = normalizer.get_normalized_name_brand_size_string()
        assert result == 'canonical-key-abc'
