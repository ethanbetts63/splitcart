import os
import json
import pytest
from products.tests.factories import ProductFactory, ProductBrandFactory
from data_management.database_updating_classes.product_updating.translation_table_generators.base_translation_table_generator import BaseTranslationTableGenerator
from data_management.database_updating_classes.product_updating.translation_table_generators.product_translation_table_generator import ProductTranslationTableGenerator
from data_management.database_updating_classes.product_updating.translation_table_generators.brand_translation_table_generator import BrandTranslationTableGenerator


# ── Concrete stub for the abstract base ──────────────────────────────────────

class StubGenerator(BaseTranslationTableGenerator):
    def __init__(self, output_path):
        super().__init__(output_path=output_path)

    def generate_translation_dict(self):
        return {'variation': 'canonical'}


# ── BaseTranslationTableGenerator ────────────────────────────────────────────

class TestBaseTranslationTableGeneratorWriteToFile:
    def test_written_content_is_valid_json(self, tmp_path):
        path = str(tmp_path / 'output.json')
        gen = StubGenerator(path)
        gen.write_to_file({'key': 'value'})
        with open(path) as f:
            assert json.load(f) == {'key': 'value'}

    def test_run_calls_generate_and_writes_file(self, tmp_path):
        path = str(tmp_path / 'output.json')
        gen = StubGenerator(path)
        gen.run()
        assert os.path.exists(path)
        with open(path) as f:
            assert json.load(f) == {'variation': 'canonical'}


# ── ProductTranslationTableGenerator ─────────────────────────────────────────

@pytest.mark.django_db
class TestProductTranslationTableGenerator:
    def test_empty_database_returns_empty_dict(self, tmp_path):
        gen = ProductTranslationTableGenerator()
        gen.output_path = str(tmp_path / 'out.json')
        assert gen.generate_translation_dict() == {}

    def test_product_with_no_variations_excluded(self, tmp_path):
        ProductFactory(normalized_name_brand_size='canonical', normalized_name_brand_size_variations=[])
        gen = ProductTranslationTableGenerator()
        gen.output_path = str(tmp_path / 'out.json')
        result = gen.generate_translation_dict()
        assert result == {}

    def test_variation_maps_to_canonical(self, tmp_path):
        ProductFactory(
            normalized_name_brand_size='canonical',
            normalized_name_brand_size_variations=['variant-a'],
        )
        gen = ProductTranslationTableGenerator()
        gen.output_path = str(tmp_path / 'out.json')
        result = gen.generate_translation_dict()
        assert result.get('variant-a') == 'canonical'

    def test_case_identical_variation_excluded(self, tmp_path):
        # 'CANONICAL' and 'canonical' differ in case but .lower() makes them equal → excluded
        ProductFactory(
            normalized_name_brand_size='canonical',
            normalized_name_brand_size_variations=['CANONICAL'],
        )
        gen = ProductTranslationTableGenerator()
        gen.output_path = str(tmp_path / 'out.json')
        result = gen.generate_translation_dict()
        assert 'CANONICAL' not in result

    def test_multiple_variations_all_mapped(self, tmp_path):
        ProductFactory(
            normalized_name_brand_size='canonical',
            normalized_name_brand_size_variations=['var-a', 'var-b'],
        )
        gen = ProductTranslationTableGenerator()
        gen.output_path = str(tmp_path / 'out.json')
        result = gen.generate_translation_dict()
        assert result['var-a'] == 'canonical'
        assert result['var-b'] == 'canonical'


# ── BrandTranslationTableGenerator ───────────────────────────────────────────

@pytest.mark.django_db
class TestBrandTranslationTableGenerator:
    def test_empty_database_returns_empty_dict(self, tmp_path):
        gen = BrandTranslationTableGenerator()
        gen.output_path = str(tmp_path / 'out.json')
        assert gen.generate_translation_dict() == {}

    def test_brand_with_no_variations_excluded(self, tmp_path):
        ProductBrandFactory(normalized_name='my-brand', normalized_name_variations=[])
        gen = BrandTranslationTableGenerator()
        gen.output_path = str(tmp_path / 'out.json')
        result = gen.generate_translation_dict()
        assert result == {}

    def test_variation_maps_to_canonical(self, tmp_path):
        ProductBrandFactory(
            normalized_name='canon-brand',
            normalized_name_variations=['alias-brand'],
        )
        gen = BrandTranslationTableGenerator()
        gen.output_path = str(tmp_path / 'out.json')
        result = gen.generate_translation_dict()
        assert result.get('alias-brand') == 'canon-brand'

    def test_self_mapping_excluded(self, tmp_path):
        ProductBrandFactory(
            normalized_name='my-brand',
            normalized_name_variations=['my-brand'],
        )
        gen = BrandTranslationTableGenerator()
        gen.output_path = str(tmp_path / 'out.json')
        result = gen.generate_translation_dict()
        assert 'my-brand' not in result


@pytest.mark.django_db
class TestBrandTranslationTableGeneratorResolveConflict:
    def test_brand_with_confirmed_prefix_wins(self, tmp_path):
        brand_with_prefix = ProductBrandFactory(normalized_name='brand-prefix')
        brand_with_prefix.confirmed_official_prefix = '0123456'
        brand_with_prefix.save()
        brand_no_prefix = ProductBrandFactory(normalized_name='brand-no-prefix')

        gen = BrandTranslationTableGenerator()
        gen.output_path = str(tmp_path / 'out.json')
        winner, loser = gen._resolve_conflict(brand_with_prefix, brand_no_prefix)
        assert winner == brand_with_prefix
        assert loser == brand_no_prefix

    def test_brand_with_more_products_wins_on_tie(self, tmp_path):
        from products.tests.factories import ProductFactory
        brand_a = ProductBrandFactory(normalized_name='brand-a')
        brand_b = ProductBrandFactory(normalized_name='brand-b')
        ProductFactory(brand=brand_a)
        ProductFactory(brand=brand_a)
        ProductFactory(brand=brand_b)

        gen = BrandTranslationTableGenerator()
        gen.output_path = str(tmp_path / 'out.json')
        winner, loser = gen._resolve_conflict(brand_a, brand_b)
        assert winner == brand_a

    def test_alphabetical_tiebreaker(self, tmp_path):
        brand_a = ProductBrandFactory(normalized_name='aardvark', name='Aardvark Brand')
        brand_z = ProductBrandFactory(normalized_name='zebra', name='Zebra Brand')

        gen = BrandTranslationTableGenerator()
        gen.output_path = str(tmp_path / 'out.json')
        winner, loser = gen._resolve_conflict(brand_a, brand_z)
        assert winner == brand_a
