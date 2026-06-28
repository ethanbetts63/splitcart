# Removed: Store Grouping System

Supermarkets like Coles, Aldi and Woolworths price nationally. The grouping system detected this and
deduplicated: once stores were confirmed to have matching prices, only the anchor store retained Price
rows, members had their prices deleted. Removed because IGA (the only per-store pricer) was removed,
making anchor deduplication pointless. The anchor resolution layer in views/utilities was also dead
once frontend store selection was removed.

See git history for all removed code.

---

## Deleted files

- `companies/models/store_group.py` — StoreGroup model: linked stores to an anchor, one per company cluster
- `companies/models/store_group_membership.py` — StoreGroupMembership model: linked a Store to a StoreGroup (OneToOne)
- `companies/views/export_anchor_stores_view.py` — internal API view returning all anchor store IDs that had prices
- `companies/tests/factories/store_group_factory.py` — Factory Boy factory for StoreGroup
- `companies/tests/factories/store_group_membership_factory.py` — Factory Boy factory for StoreGroupMembership
- `companies/tests/model_tests/test_store_group_model.py` — StoreGroup model tests
- `companies/tests/model_tests/test_store_group_membership_model.py` — StoreGroupMembership model tests
- `companies/tests/view_tests/test_export_anchor_stores_view.py` — export anchor stores view tests
- `products/utils/get_pricing_stores.py` — resolved store IDs to anchor IDs, with 1-hour company-level cache
- `products/tests/factories/store_group_factory.py` — products-app copy of StoreGroup/StoreGroupMembership factories
- `products/tests/conftest.py` — contained only the `make_anchored_store` fixture
- `products/tests/util_tests/test_get_pricing_stores.py` — tests for anchor resolution logic
- `data_management/database_updating_classes/product_updating/group_maintanance/` (directory):
  - `group_maintenance_orchestrator.py` — ran InternalGroupHealthChecker then IntergroupComparer in sequence
  - `internal_group_health_checker.py` — compared each member's prices against the anchor; ejected mismatches, deleted redundant prices for matches
  - `intergroup_comparer.py` — compared anchor-to-anchor across groups; merged groups with ≥98% price overlap
- `data_management/management/commands/inspect_store_groups.py` — management command reporting store/group counts per company
- `data_management/utils/generation_utils/store_groups_generator.py` — reset all StoreGroups and created one per Store
- `data_management/analysers/store_grouping.py` — entry point for price-correlation-based group analysis
- `data_management/utils/analysis_utils/store_grouping_utils/` (directory):
  - `data_fetching.py` — fetched per-store price dicts for correlation analysis
  - `graph_construction.py` — built adjacency graph of stores with ≥threshold% price overlap
  - `grouping.py` — connected-components traversal on the correlation graph
- `data_management/tests/util_tests/test_intergroup_comparer.py`
- `data_management/tests/util_tests/test_internal_group_health_checker.py`
- `data_management/tests/util_tests/test_grouping.py`
- `data_management/tests/util_tests/test_graph_construction.py`
- `data_management/utils/geospatial_utils.py` — haversine distance + nearby-store query; used by DefaultStoresGenerator pre-simplification
- `data_management/tests/util_tests/test_geospatial_utils.py`

## Modified files

- `products/models/price.py` — removed `PriceQuerySet` class (contained `for_stores()` which called `get_pricing_stores_map`); Price now uses default manager
- `data_management/utils/cart_optimization/substitute_manager.py` — replaced `Price.objects.for_stores(store_ids)` with direct `store_id__in` filter
- `data_management/utils/generation_utils/default_stores_generator.py` — was postcode-based geospatial search for anchor stores; simplified to `Price.objects.values_list('store_id').distinct()`
- `data_management/utils/generation_utils/store_stats_generator.py` — removed anchor-based queries; uses direct `Price.objects.filter(store__company=company)` queries
- `data_management/database_updating_classes/product_updating/update_orchestrator.py` — removed `GroupMaintenanceOrchestrator` import and call from post-processing
- `data_management/management/commands/generate.py` — removed `--store-groups` argument and handler
- `companies/models/__init__.py` — removed `StoreGroup`, `StoreGroupMembership` exports
- `companies/admin.py` — removed `StoreGroupAdmin`
- `companies/urls.py` — removed `export/anchor-stores/` URL
- `companies/tests/factories/__init__.py` — removed `StoreGroupFactory`, `StoreGroupMembershipFactory`
- `products/tests/factories/__init__.py` — removed `StoreGroupFactory`, `StoreGroupMembershipFactory` import
- `products/tests/model_tests/test_price_model.py` — removed 3 tests using `Price.objects.for_stores()` and `make_anchored_store`
- `data_management/tests/command_tests/test_generate_command.py` — removed `test_store_groups_flag`

---
---

# Removed: Store & Division Models

With national pricing (one price per company across Australia), the Store model became an unnecessary
indirection between Price and Company. The entire store-discovery and scheduling infrastructure existed
to support per-location scraping, which is no longer needed. Price now has a direct FK to Company.
The scraper uses a hardcoded API store_id per company instead of querying Store records.

See git history for all removed code.

---

## companies/ — models, serializers, views, tests

- `companies/models/store.py` — Store model with address, lat/long, scraping schedule fields (last_scraped, needs_rescraping, scheduled_at), and external store_id for API calls
- `companies/models/division.py` — Division model: subdivision of a company (e.g. "Coles Supermarkets"), used by SchedulerView to filter eligible stores
- `companies/serializers/store_serializer.py` — basic Store serializer
- `companies/serializers/store_export_serializer.py` — Store export serializer for internal API
- `companies/views/export_stores_view.py` — internal API view to export all store records
- `companies/tests/factories/store_factory.py` — Factory Boy factory for Store
- `companies/tests/factories/division_factory.py` — Factory Boy factory for Division
- `companies/tests/model_tests/test_store_model.py` — Store model tests
- `companies/tests/model_tests/test_division_model.py` — Division model tests
- `companies/tests/serializer_tests/test_store_serializer.py` — Store serializer tests
- `companies/tests/serializer_tests/test_store_export_serializer.py` — Store export serializer tests
- `companies/tests/view_tests/test_export_stores_view.py` — export stores view tests

## scraping/ — store discovery

- `scraping/management/commands/find_stores.py` — management command to discover and save physical store locations for each company via their APIs
- `scraping/scrapers/base_store_scraper.py` — abstract base class for store location scrapers
- `scraping/scrapers/store_scraper_aldi.py` — scraper for Aldi store locations
- `scraping/scrapers/store_scraper_coles.py` — scraper for Coles store locations
- `scraping/scrapers/store_scraper_woolworths.py` — scraper for Woolworths store locations
- `scraping/utils/shop_scraping_utils/BaseStoreCleaner.py` — base class for normalising raw store API responses
- `scraping/utils/shop_scraping_utils/StoreCleanerAldi.py` — cleans raw Aldi store API data
- `scraping/utils/shop_scraping_utils/StoreCleanerColes.py` — cleans raw Coles store API data
- `scraping/utils/shop_scraping_utils/StoreCleanerWoolworths.py` — cleans raw Woolworths store API data
- `scraping/utils/shop_scraping_utils/get_graphql_query.py` — builds GraphQL queries used by store scrapers
- `scraping/utils/shop_scraping_utils/store_field_maps.py` — field mapping configs for store data cleaning
- `scraping/utils/command_utils/store_uploader.py` — uploaded cleaned store data to the Django API
- `scraping/tests/util_tests/test_base_store_cleaner.py`
- `scraping/tests/util_tests/test_store_cleaner_aldi.py`
- `scraping/tests/util_tests/test_store_cleaner_coles.py`
- `scraping/tests/util_tests/test_store_cleaner_woolworths.py`
- `scraping/tests/util_tests/test_store_uploader.py`

## data_management/ — scheduling, store updating, analysis

- `data_management/views/scheduler_view.py` — internal API endpoint returning the next store to scrape, with priority logic: never-scraped → needs_rescraping flag → oldest last_scraped
- `data_management/database_updating_classes/archive_store_updater.py` — updated Store records from archived store data files
- `data_management/database_updating_classes/discovery_store_updater.py` — created/updated Store records from freshly scraped store discovery data
- `data_management/database_updating_classes/discovery_update_orchestrator.py` — orchestrated processing of store discovery inbox files via DiscoveryStoreUpdater
- `data_management/management/commands/compare_stores.py` — management command to compare product overlap between two stores by PK
- `data_management/management/commands/inspect_stores.py` — management command to display store info and price counts per company
- `data_management/utils/analysis_utils/pricing_analysis/get_product_prices_by_store.py` — fetched per-store price breakdowns for a product
- `data_management/analysers/store_pricing_heatmap.py` — generated a heatmap of price coverage across stores
- `data_management/analysers/store_product_overlap.py` — analysed product catalog overlap between stores
- `data_management/utils/generation_utils/store_stats_generator.py` — per-store health report showing how many stores had fresh price data per company; replaced with company-level report

## Files replaced or significantly changed

- `products/utils/default_stores.py` → replaced by `products/utils/default_companies.py`; same cache pattern, returns company IDs instead of store IDs; SystemSetting key changed from `default_pricing_stores` to `default_pricing_companies`
- `data_management/utils/generation_utils/default_companies_generator.py` → updated to query by company and write `default_pricing_companies` SystemSetting key
- `scraping/management/commands/scrape.py` — simplified from a multi-store scheduler loop (querying hundreds of Store records) to hardcoded single API store_id per company; no longer imports Store model
- `data_management/database_updating_classes/product_updating/update_orchestrator.py` — store resolution (`Store.objects.get(store_id=...)`) replaced with company resolution (`Company.objects.get(name=...)`) from JSONL metadata

## Architectural changes

- `products/models/price.py`: `store` FK (→ Store) replaced with `company` FK (→ Company); `unique_together` changed from `('product', 'store')` to `('product', 'company')`
- JSONL scraper metadata: `store_id` field replaced with `company_name`; orchestrator resolves Company by name
- All ORM traversals updated: `prices__store__id__in=store_ids` → `prices__company__id__in=company_ids`
- All attribute access updated: `price.store.company.name` → `price.company.name`
- `nearby_store_ids` removed from serializer context entirely; `ProductSerializer` now always returns all prices (one per company)
- Cart optimization (`users/utils/cart_optimization.py`, `build_price_slots.py`) updated to resolve companies directly; `_translate_shopping_plan` removed (no anchor→original mapping needed)
- `SubstituteManager` updated from `store_ids` to `company_ids`
