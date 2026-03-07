import datetime
import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from products.tests.factories import ProductFactory, PriceFactory
from companies.tests.factories import StoreFactory
from data_management.database_updating_classes.product_updating.update_orchestrator import UpdateOrchestrator


@pytest.fixture
def orchestrator(mock_command):
    return UpdateOrchestrator(mock_command)


# ── update_cache ──────────────────────────────────────────────────────────────

class TestUpdateCache:
    def test_adds_value_to_existing_cache(self, orchestrator):
        orchestrator.caches['products_by_norm_string'] = {}
        orchestrator.update_cache('products_by_norm_string', 'milk', 42)
        assert orchestrator.caches['products_by_norm_string']['milk'] == 42

    def test_ignores_unknown_cache_name(self, orchestrator):
        # Should not raise
        orchestrator.update_cache('nonexistent_cache', 'key', 'value')


# ── _deduplicate_product_data_for_pricing ─────────────────────────────────────

class TestDeduplicateProductDataForPricing:
    def _make_raw(self, nnbs):
        return {'product': {'normalized_name_brand_size': nnbs}}

    def test_returns_all_when_no_duplicates(self, orchestrator):
        orchestrator.caches['products_by_norm_string'] = {'milk': 1, 'eggs': 2}
        raw = [self._make_raw('milk'), self._make_raw('eggs')]
        result = orchestrator._deduplicate_product_data_for_pricing(raw)
        assert len(result) == 2

    def test_deduplicates_same_canonical_id(self, orchestrator):
        # Both 'milk-brand-a' and 'milk-alias' map to the same product ID
        orchestrator.caches['products_by_norm_string'] = {'milk-brand-a': 1, 'milk-alias': 1}
        raw = [self._make_raw('milk-brand-a'), self._make_raw('milk-alias')]
        result = orchestrator._deduplicate_product_data_for_pricing(raw)
        assert len(result) == 1

    def test_unknown_product_kept_once(self, orchestrator):
        orchestrator.caches['products_by_norm_string'] = {}
        raw = [self._make_raw('unknown-x'), self._make_raw('unknown-x')]
        result = orchestrator._deduplicate_product_data_for_pricing(raw)
        assert len(result) == 1

    def test_skips_entries_with_no_product_dict(self, orchestrator):
        orchestrator.caches['products_by_norm_string'] = {}
        raw = [{'product': {}}, {'product': None}, {}]
        result = orchestrator._deduplicate_product_data_for_pricing(raw)
        assert len(result) == 0


# ── _is_file_valid ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestIsFileValid:
    def test_empty_metadata_returns_false(self, orchestrator):
        valid, store = orchestrator._is_file_valid(None, [{'product': {}}])
        assert valid is False
        assert store is None

    def test_empty_raw_data_returns_false(self, orchestrator):
        valid, store = orchestrator._is_file_valid({'store_id': 'x', 'scraped_date': '2025-01-01T00:00:00'}, [])
        assert valid is False
        assert store is None

    def test_unknown_store_returns_false(self, orchestrator):
        valid, store = orchestrator._is_file_valid(
            {'store_id': 'nonexistent-store', 'scraped_date': '2025-01-01T00:00:00'},
            [{'product': {}}]
        )
        assert valid is False
        assert store is None

    def test_missing_scraped_date_returns_false(self, orchestrator):
        db_store = StoreFactory()
        valid, store = orchestrator._is_file_valid(
            {'store_id': db_store.store_id},
            [{'product': {}}]
        )
        assert valid is False

    def test_invalid_scraped_date_returns_false(self, orchestrator):
        db_store = StoreFactory()
        valid, store = orchestrator._is_file_valid(
            {'store_id': db_store.store_id, 'scraped_date': 'not-a-date'},
            [{'product': {}}]
        )
        assert valid is False

    def test_stale_date_returns_false(self, orchestrator):
        product = ProductFactory()
        db_store = StoreFactory()
        PriceFactory(
            product=product, store=db_store,
            scraped_date=datetime.date(2025, 6, 1),
        )
        # Incoming date is older than the latest DB price
        valid, store = orchestrator._is_file_valid(
            {'store_id': db_store.store_id, 'scraped_date': '2025-01-01T00:00:00'},
            [{'product': {}}]
        )
        assert valid is False

    def test_partial_scrape_returns_false(self, orchestrator):
        product = ProductFactory()
        db_store = StoreFactory()
        # Fill DB with 10 prices
        for _ in range(10):
            p = ProductFactory()
            PriceFactory(product=p, store=db_store, scraped_date=datetime.date(2024, 1, 1))

        # File has only 1 product — less than 90% of 10
        valid, store = orchestrator._is_file_valid(
            {'store_id': db_store.store_id, 'scraped_date': '2025-06-01T00:00:00'},
            [{'product': {}}]
        )
        assert valid is False

    def test_valid_file_returns_true_and_store(self, orchestrator):
        db_store = StoreFactory()
        valid, store = orchestrator._is_file_valid(
            {'store_id': db_store.store_id, 'scraped_date': '2025-06-01T00:00:00'},
            [{'product': {}}]
        )
        assert valid is True
        assert store.pk == db_store.pk

    def test_valid_file_with_existing_prices_passes_count_check(self, orchestrator):
        db_store = StoreFactory()
        # 5 prices in DB, file has 5 items — exactly 100%
        products = [ProductFactory() for _ in range(5)]
        for p in products:
            PriceFactory(product=p, store=db_store, scraped_date=datetime.date(2024, 1, 1))

        raw = [{'product': {}} for _ in range(5)]
        valid, store = orchestrator._is_file_valid(
            {'store_id': db_store.store_id, 'scraped_date': '2025-06-01T00:00:00'},
            raw
        )
        assert valid is True
