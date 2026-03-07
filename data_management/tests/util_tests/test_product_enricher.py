import types
from data_management.database_updating_classes.product_updating.post_processing.product_enricher import ProductEnricher


def _product(**kwargs):
    """Create a simple object with product-like attributes."""
    defaults = {
        'barcode': None,
        'url': None,
        'aldi_image_url': None,
        'has_no_coles_barcode': False,
        'sizes': [],
        'normalized_name_brand_size': 'product-canonical',
        'normalized_name_brand_size_variations': [],
        'brand_name_company_pairs': [],
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


class TestProductEnricher:
    def test_returns_false_when_nothing_to_enrich(self):
        canon = _product()
        dupe = _product()
        result = ProductEnricher.enrich_canonical_product(canon, dupe)
        assert result is False

    def test_fills_barcode_from_duplicate_when_canonical_blank(self):
        canon = _product(barcode=None)
        dupe = _product(barcode='9310072001646')
        ProductEnricher.enrich_canonical_product(canon, dupe)
        assert canon.barcode == '9310072001646'

    def test_does_not_overwrite_existing_barcode(self):
        canon = _product(barcode='existing')
        dupe = _product(barcode='new_barcode')
        ProductEnricher.enrich_canonical_product(canon, dupe)
        assert canon.barcode == 'existing'

    def test_fills_url_from_duplicate_when_canonical_blank(self):
        canon = _product(url=None)
        dupe = _product(url='https://example.com/product')
        ProductEnricher.enrich_canonical_product(canon, dupe)
        assert canon.url == 'https://example.com/product'

    def test_does_not_overwrite_existing_url(self):
        canon = _product(url='https://original.com')
        dupe = _product(url='https://new.com')
        ProductEnricher.enrich_canonical_product(canon, dupe)
        assert canon.url == 'https://original.com'

    def test_fills_aldi_image_url_from_duplicate_when_blank(self):
        canon = _product(aldi_image_url=None)
        dupe = _product(aldi_image_url='https://aldi.com/img.jpg')
        ProductEnricher.enrich_canonical_product(canon, dupe)
        assert canon.aldi_image_url == 'https://aldi.com/img.jpg'

    def test_has_no_coles_barcode_true_wins(self):
        canon = _product(has_no_coles_barcode=False)
        dupe = _product(has_no_coles_barcode=True)
        result = ProductEnricher.enrich_canonical_product(canon, dupe)
        assert canon.has_no_coles_barcode is True
        assert result is True

    def test_has_no_coles_barcode_stays_false_when_dupe_is_false(self):
        canon = _product(has_no_coles_barcode=False)
        dupe = _product(has_no_coles_barcode=False)
        ProductEnricher.enrich_canonical_product(canon, dupe)
        assert canon.has_no_coles_barcode is False

    def test_merges_sizes(self):
        canon = _product(sizes=['500g'])
        dupe = _product(sizes=['1kg'])
        ProductEnricher.enrich_canonical_product(canon, dupe)
        assert set(canon.sizes) == {'500g', '1kg'}

    def test_does_not_duplicate_sizes(self):
        canon = _product(sizes=['500g'])
        dupe = _product(sizes=['500g'])
        ProductEnricher.enrich_canonical_product(canon, dupe)
        assert canon.sizes.count('500g') == 1

    def test_merges_normalized_name_brand_size_variations(self):
        canon = _product(
            normalized_name_brand_size='product-canonical',
            normalized_name_brand_size_variations=['variant-a'],
        )
        dupe = _product(
            normalized_name_brand_size='variant-b',
            normalized_name_brand_size_variations=['variant-c'],
        )
        ProductEnricher.enrich_canonical_product(canon, dupe)
        assert 'variant-b' in canon.normalized_name_brand_size_variations
        assert 'variant-c' in canon.normalized_name_brand_size_variations

    def test_canonical_name_not_added_to_variations(self):
        canon = _product(normalized_name_brand_size='canonical')
        dupe = _product(normalized_name_brand_size='canonical')
        ProductEnricher.enrich_canonical_product(canon, dupe)
        assert 'canonical' not in (canon.normalized_name_brand_size_variations or [])

    def test_merges_brand_name_company_pairs(self):
        canon = _product(brand_name_company_pairs=[['BrandA', 'Coles']])
        dupe = _product(brand_name_company_pairs=[['BrandB', 'Woolworths']])
        ProductEnricher.enrich_canonical_product(canon, dupe)
        companies = [pair[1] for pair in canon.brand_name_company_pairs]
        assert 'Coles' in companies
        assert 'Woolworths' in companies

    def test_does_not_duplicate_brand_company_pairs(self):
        pair = ['BrandA', 'Coles']
        canon = _product(brand_name_company_pairs=[pair])
        dupe = _product(brand_name_company_pairs=[pair])
        ProductEnricher.enrich_canonical_product(canon, dupe)
        companies = [p[1] for p in canon.brand_name_company_pairs]
        assert companies.count('Coles') == 1

    def test_returns_true_when_change_made(self):
        canon = _product(barcode=None)
        dupe = _product(barcode='123456')
        result = ProductEnricher.enrich_canonical_product(canon, dupe)
        assert result is True
