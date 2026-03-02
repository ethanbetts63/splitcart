import pytest
from scraping.utils.product_scraping_utils.size_comparer import SizeComparer


class MockProduct:
    """Minimal stand-in for a Product model instance."""
    def __init__(self, name='', brand='', size=''):
        self.name = name
        self.brand = brand
        self.size = size


@pytest.fixture
def comparer():
    return SizeComparer()


class TestGetCanonicalSizes:
    def test_extracts_grams(self, comparer):
        product = MockProduct(name='Milk 500g')
        sizes = comparer.get_canonical_sizes(product)
        assert (500.0, 'g') in sizes

    def test_extracts_litres_as_ml(self, comparer):
        product = MockProduct(name='Juice 2L')
        sizes = comparer.get_canonical_sizes(product)
        assert (2000.0, 'ml') in sizes

    def test_no_size_returns_empty_set(self, comparer):
        product = MockProduct(name='Unknown Product')
        sizes = comparer.get_canonical_sizes(product)
        assert sizes == set()


class TestAreSizesCompatible:
    def test_same_size_is_compatible(self, comparer):
        p1 = MockProduct(name='Product 500g')
        p2 = MockProduct(name='Item 500g')
        assert comparer.are_sizes_compatible(p1, p2) is True

    def test_within_tolerance_is_compatible(self, comparer):
        # 490g vs 500g — within 10% of 490
        p1 = MockProduct(name='Product 490g')
        p2 = MockProduct(name='Item 500g')
        assert comparer.are_sizes_compatible(p1, p2) is True

    def test_outside_tolerance_is_not_compatible(self, comparer):
        p1 = MockProduct(name='Product 100g')
        p2 = MockProduct(name='Item 500g')
        assert comparer.are_sizes_compatible(p1, p2) is False

    def test_different_units_is_not_compatible(self, comparer):
        p1 = MockProduct(name='Product 500g')
        p2 = MockProduct(name='Item 500ml')
        assert comparer.are_sizes_compatible(p1, p2) is False

    def test_pack_exact_match_is_compatible(self, comparer):
        p1 = MockProduct(size='6pk')
        p2 = MockProduct(size='6pk')
        assert comparer.are_sizes_compatible(p1, p2) is True

    def test_pack_different_count_is_not_compatible(self, comparer):
        p1 = MockProduct(size='6pk')
        p2 = MockProduct(size='12pk')
        assert comparer.are_sizes_compatible(p1, p2) is False

    def test_no_sizes_returns_false(self, comparer):
        p1 = MockProduct(name='Unknown')
        p2 = MockProduct(name='Unknown2')
        assert comparer.are_sizes_compatible(p1, p2) is False


class TestAreSizesDifferent:
    def test_different_sizes_returns_true(self, comparer):
        p1 = MockProduct(name='Product 500g')
        p2 = MockProduct(name='Item 1kg')
        assert comparer.are_sizes_different(p1, p2) is True

    def test_same_sizes_returns_false(self, comparer):
        p1 = MockProduct(name='Product 500g')
        p2 = MockProduct(name='Item 500g')
        assert comparer.are_sizes_different(p1, p2) is False

    def test_no_sizes_returns_false(self, comparer):
        p1 = MockProduct(name='Unknown')
        p2 = MockProduct(name='Unknown2')
        assert comparer.are_sizes_different(p1, p2) is False
