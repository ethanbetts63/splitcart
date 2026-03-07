import pytest
from products.models import ProductBrand, Product
from products.tests.factories import ProductFactory, ProductBrandFactory
from data_management.database_updating_classes.gs1_update_orchestrator import GS1UpdateOrchestrator


@pytest.fixture
def orchestrator(mock_command):
    return GS1UpdateOrchestrator(mock_command)


@pytest.mark.django_db
class TestGS1UpdateOrchestratorProcessRecord:
    def test_missing_key_skips_record(self, orchestrator):
        orchestrator._process_record({'confirmed_company_name': 'Cadbury'})
        assert not ProductBrand.objects.exists()

    def test_missing_name_skips_record(self, orchestrator):
        orchestrator._process_record({'confirmed_license_key': '0123456'})
        assert not ProductBrand.objects.exists()

    def test_creates_new_canonical_brand(self, orchestrator):
        orchestrator._process_record({
            'confirmed_license_key': '0123456',
            'confirmed_company_name': 'Cadbury',
        })
        assert ProductBrand.objects.filter(confirmed_official_prefix='0123456').exists()

    def test_sets_prefix_on_existing_brand(self, orchestrator):
        brand = ProductBrandFactory(normalized_name='cadbury', name='Cadbury', confirmed_official_prefix=None)
        orchestrator._process_record({
            'confirmed_license_key': '0123456',
            'confirmed_company_name': 'Cadbury',
        })
        brand.refresh_from_db()
        assert brand.confirmed_official_prefix == '0123456'

    def test_does_not_duplicate_brand(self, orchestrator):
        ProductBrandFactory(normalized_name='cadbury', name='Cadbury')
        orchestrator._process_record({
            'confirmed_license_key': '0123456',
            'confirmed_company_name': 'Cadbury',
        })
        assert ProductBrand.objects.filter(normalized_name='cadbury').count() == 1

    def test_adds_incorrect_brand_as_variation(self, orchestrator):
        canonical = ProductBrandFactory(normalized_name='cadbury', name='Cadbury')
        wrong_brand = ProductBrandFactory(normalized_name='cadbury-au', name='Cadbury AU')
        ProductFactory(brand=wrong_brand, barcode='01234560001')

        orchestrator._process_record({
            'confirmed_license_key': '0123456',
            'confirmed_company_name': 'Cadbury',
        })

        canonical.refresh_from_db()
        assert 'Cadbury AU' in canonical.name_variations

    def test_links_brandless_products_to_canonical(self, orchestrator):
        product = ProductFactory(brand=None, barcode='01234560001')

        orchestrator._process_record({
            'confirmed_license_key': '0123456',
            'confirmed_company_name': 'Nestle',
        })

        product.refresh_from_db()
        assert product.brand is not None
        assert product.brand.normalized_name == 'nestle'

    def test_no_action_when_no_inconsistent_products(self, orchestrator):
        canonical = ProductBrandFactory(normalized_name='vegemite', name='Vegemite')
        # Products exist but belong to the canonical brand already
        ProductFactory(brand=canonical, barcode='09876540001')

        orchestrator._process_record({
            'confirmed_license_key': '0987654',
            'confirmed_company_name': 'Vegemite',
        })

        canonical.refresh_from_db()
        # name_variations should remain empty (no incorrect brands)
        assert not canonical.name_variations or 'Vegemite' not in canonical.name_variations
