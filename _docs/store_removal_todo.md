# Store & Division Removal — Task List

Removing the `Store` and `Division` models entirely. `Price.store` FK becomes `Price.company` FK.
Scrapers continue to use a hardcoded external API store_id per company for HTTP calls, but nothing hits the DB Store table anymore.

Work bottom-up: foundational model/data changes first, then pipeline, then product app, then cart/optimization, then cleanup.

---

## 0. Pre-flight

- [ ] Query DB for one external store_id per company to hardcode in scrape.py:
  ```
  ./venv/Scripts/python manage.py shell -c "from companies.models import Store; [print(s.company.name, repr(s.store_id)) for s in Store.objects.select_related('company').order_by('company__name', 'pk')[:10]]"
  ```
  Note the values — you'll need them in Step 4.

---

## 1. Delete files

Delete all of these — no code to save, use git history if needed.

**companies/**
- [ ] `companies/models/store.py`
- [ ] `companies/models/division.py`
- [ ] `companies/serializers/store_serializer.py`
- [ ] `companies/serializers/store_export_serializer.py`
- [ ] `companies/views/export_stores_view.py`
- [ ] `companies/tests/factories/store_factory.py`
- [ ] `companies/tests/factories/division_factory.py`
- [ ] `companies/tests/model_tests/test_store_model.py`
- [ ] `companies/tests/model_tests/test_division_model.py`
- [ ] `companies/tests/serializer_tests/test_store_serializer.py`
- [ ] `companies/tests/serializer_tests/test_store_export_serializer.py`
- [ ] `companies/tests/view_tests/test_export_stores_view.py`

**scraping/**
- [ ] `scraping/management/commands/find_stores.py`
- [ ] `scraping/scrapers/base_store_scraper.py`
- [ ] `scraping/scrapers/store_scraper_aldi.py`
- [ ] `scraping/scrapers/store_scraper_coles.py`
- [ ] `scraping/scrapers/store_scraper_woolworths.py`
- [ ] `scraping/utils/shop_scraping_utils/BaseStoreCleaner.py`
- [ ] `scraping/utils/shop_scraping_utils/StoreCleanerAldi.py`
- [ ] `scraping/utils/shop_scraping_utils/StoreCleanerColes.py`
- [ ] `scraping/utils/shop_scraping_utils/StoreCleanerWoolworths.py`
- [ ] `scraping/utils/shop_scraping_utils/get_graphql_query.py`
- [ ] `scraping/utils/shop_scraping_utils/store_field_maps.py`
- [ ] `scraping/utils/command_utils/store_uploader.py`
- [ ] `scraping/tests/util_tests/test_base_store_cleaner.py`
- [ ] `scraping/tests/util_tests/test_store_cleaner_aldi.py`
- [ ] `scraping/tests/util_tests/test_store_cleaner_coles.py`
- [ ] `scraping/tests/util_tests/test_store_cleaner_woolworths.py`
- [ ] `scraping/tests/util_tests/test_store_uploader.py`

**data_management/**
- [ ] `data_management/views/scheduler_view.py`
- [ ] `data_management/database_updating_classes/archive_store_updater.py`
- [ ] `data_management/database_updating_classes/discovery_store_updater.py`
- [ ] `data_management/database_updating_classes/discovery_update_orchestrator.py`
- [ ] `data_management/management/commands/compare_stores.py`
- [ ] `data_management/management/commands/inspect_stores.py`
- [ ] `data_management/utils/analysis_utils/pricing_analysis/get_product_prices_by_store.py`
- [ ] `data_management/utils/generation_utils/store_stats_generator.py`
- [ ] `data_management/analysers/store_pricing_heatmap.py` (if exists)
- [ ] `data_management/analysers/store_product_overlap.py` (if exists)
- [ ] `data_management/utils/analysis_utils/store_location_plotter.py` (if exists)

**products/**
- [ ] `products/utils/default_stores.py`

---

## 2. Core model change — Price

File: `products/models/price.py`

- [ ] Remove `store = models.ForeignKey('companies.Store', ...)` 
- [ ] Add `company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='prices')`
- [ ] Change `unique_together = ('product', 'store')` → `('product', 'company')`
- [ ] Change index `fields=['store', 'product']` → `fields=['company', 'product']`
- [ ] Update `__str__`: `price.store.store_name` → `price.company.name`

---

## 3. New default_companies helper

- [ ] Create `products/utils/default_companies.py`:
  ```python
  from django.core.cache import cache
  from data_management.models import SystemSetting

  CACHE_KEY = 'default_pricing_companies'

  def get_default_company_ids() -> list[int]:
      company_ids = cache.get(CACHE_KEY)
      if company_ids is None:
          try:
              setting = SystemSetting.objects.get(key=CACHE_KEY)
              company_ids = setting.value
              cache.set(CACHE_KEY, company_ids, 60 * 60)
          except SystemSetting.DoesNotExist:
              company_ids = []
      return company_ids
  ```

---

## 4. Update companies/ wiring

- [ ] `companies/models/__init__.py` — remove `from .division import Division` and `from .store import Store`
- [ ] `companies/admin.py` — remove Division and Store imports and their `@admin.register` blocks
- [ ] `companies/urls.py` — remove `export/stores/` path and `ExportStoresView` import
- [ ] `companies/tests/factories/__init__.py` — remove StoreFactory and DivisionFactory imports and `__all__` entries

---

## 5. Update data_management pipeline

### default_stores_generator.py → DefaultCompaniesGenerator
File: `data_management/utils/generation_utils/default_stores_generator.py`

- [ ] Rename class `DefaultStoresGenerator` → `DefaultCompaniesGenerator`
- [ ] Change `SETTING_KEY = 'default_anchor_stores'` → `'default_pricing_companies'`
- [ ] Change `Price.objects.values_list('store_id', flat=True).distinct()` → `Price.objects.values_list('company_id', flat=True).distinct()`
- [ ] Update log messages

### PriceManager
File: `data_management/database_updating_classes/product_updating/price_manager.py`

- [ ] Change `process(self, raw_product_data, store)` → `process(self, raw_product_data, company)`
- [ ] Change `'store': store` in price_data dict → `'company': company`
- [ ] Change cache key `prices_by_store` → `prices_by_company`, `store.id` → `company.id`
- [ ] Remove `store.last_scraped = ...; store.save(...)` at end (Company has no such field)
- [ ] Update all log messages replacing "store" with "company"

### UpdateOrchestrator
File: `data_management/database_updating_classes/product_updating/update_orchestrator.py`

- [ ] Remove `Store` import, keep `Company`
- [ ] Rename `_prepare_price_cache_for_store(self, store)` → `_prepare_price_cache_for_company(self, company)`
  - `Price.objects.filter(store=store)` → `Price.objects.filter(company=company)`
  - cache key: `prices_by_company[company.id]`
- [ ] In `_build_global_caches`: rename `'prices_by_store'` → `'prices_by_company'`
- [ ] In `_is_file_valid`: replace `Store.objects.get(store_id=metadata['store_id'])` with `Company.objects.get(name=metadata['company_name'])`. Return the company object.
- [ ] In `run()`: `store = store_or_reason` → `company = store_or_reason`; `store.company.id` → `company.id`; call `_prepare_price_cache_for_company(company)`; pass `company` to `price_manager.process()`, `product_manager.process()`, `path_manager.process()`

### generate.py management command
File: `data_management/management/commands/generate.py`

- [ ] Update import: `DefaultStoresGenerator` → `DefaultCompaniesGenerator`
- [ ] Update `--default-stores` argument label/handler if it exists (rename to `--default-companies`)
- [ ] Remove any `--store-stats` argument and its handler (StoreStatsGenerator deleted)

### upload.py management command
File: `data_management/management/commands/upload.py`

- [ ] Remove any reference to `DiscoveryUpdateOrchestrator`, `ArchiveStoreUpdater`, or store inbox logic

### data_management/urls.py
- [ ] Remove the scheduler URL entry and `SchedulerView` import

---

## 6. Update scraping system

### JSONL writer metadata
File: `scraping/utils/product_scraping_utils/jsonl_writer.py`

- [ ] Change metadata field from `store_id` to `company_name` (orchestrator now resolves Company by name, not Store by store_id)

### scrape.py — simplify to hardcoded single store per company
File: `scraping/management/commands/scrape.py`

- [ ] Remove `Store` import
- [ ] Add three module-level constants with the values from Step 0:
  ```python
  COLES_STORE_ID = '<value>'
  WOOLWORTHS_STORE_ID = '<value>'
  ALDI_STORE_ID = '<value>'
  ```
- [ ] Remove `_run_coles_scraper`, `_run_scheduler_worker`, `_scrape_single_store` methods
- [ ] Replace with simple `_scrape_coles()`, `_scrape_woolworths()`, `_scrape_aldi()` methods each using the hardcoded store_id
- [ ] Remove `--store-pk`, `--coles-v3` (or keep v3 if useful)
- [ ] Remove all Store DB queries

### scraping/utils/product_scraping_utils/output_utils.py
- [ ] Change `store_name` display field → `company_name` (cosmetic, for progress output)

### base_product_scraper.py
- [ ] Read file — update any store-specific DB references if present (API usage of store_id is fine to keep)

---

## 7. Update products app

### ProductSerializer
File: `products/serializers/product_serializer.py`

- [ ] In `_get_filtered_prices`: remove `prices_map` branch (dead) and `nearby_store_ids` filtering — just return `list(obj.prices.all())`
- [ ] In `get_image_url`: `price.store and price.store.company` → `price.company`; `company = price.store.company` → `company = price.company`
- [ ] In `get_prices`: `price_obj.store.company.name` → `price_obj.company.name`; `p.store.company.name == company_name` → `p.company.name == company_name`

### bargain_utils.py
File: `products/utils/bargain_utils.py`

- [ ] Function signature: `calculate_bargains(product_ids, store_ids)` → `calculate_bargains(product_ids, company_ids)`
- [ ] `store_id__in=store_ids` → `company_id__in=company_ids`
- [ ] `.select_related('store__company')` → `.select_related('company')`
- [ ] `p.store.company_id` → `p.company_id`
- [ ] `min_price_obj.store.store_name` → `min_price_obj.company.name`
- [ ] `min_price_obj.store.company.name` → `min_price_obj.company.name`

### product_ordering.py
File: `products/utils/product_ordering.py`

- [ ] Rename param `anchor_store_ids` → `company_ids` throughout
- [ ] `prices__store__id__in=anchor_store_ids` → `prices__company__id__in=company_ids`
- [ ] `store_id__in=anchor_store_ids` → `company_id__in=company_ids`
- [ ] `.select_related('store__company')` → `.select_related('company')`
- [ ] `p.store.company_id` → `p.company_id`
- [ ] `min_price_obj.store.store_name` / `.store.company.name` → `min_price_obj.company.name`

### product_list_view.py
File: `products/views/product_list_view.py`

- [ ] Replace `from products.utils.default_stores import get_default_store_ids` → `from products.utils.default_companies import get_default_company_ids`
- [ ] Rename all `store_ids` vars → `company_ids`
- [ ] `get_default_store_ids()` → `get_default_company_ids()`
- [ ] `prices__store__id__in=store_ids` → `prices__company__id__in=company_ids`
- [ ] `'prices__store__company'` prefetch → `'prices__company'`
- [ ] Remove `'nearby_store_ids'` from serializer context (serializer no longer uses it)
- [ ] `calculate_bargains(..., store_ids)` → `calculate_bargains(..., company_ids)`

### bargain_carousel_view.py
File: `products/views/bargain_carousel_view.py`

- [ ] Replace default_stores import → default_companies
- [ ] Rename all `store_ids` vars → `company_ids`
- [ ] `product__prices__store__id__in=store_ids` → `product__prices__company__id__in=company_ids`
- [ ] `'prices__store__company'` prefetch → `'prices__company'`
- [ ] Remove `'nearby_store_ids'` from serializer context
- [ ] `calculate_bargains(..., store_ids)` → `calculate_bargains(..., company_ids)`

### product_detail_view.py
File: `products/views/product_detail_view.py`

- [ ] `'prices__store__company'` → `'prices__company'` in prefetch_related

### export_prices_view.py
File: `products/views/export_prices_view.py`

- [ ] `store_id__in=store_ids` → `company_id__in=company_ids`
- [ ] `store__company_id` → `company_id`
- [ ] `store_ids_str` / `store_ids` param → `company_ids_str` / `company_ids`

---

## 8. Update cart optimization

### substitute_manager.py
File: `data_management/utils/cart_optimization/substitute_manager.py`

- [ ] `__init__(self, product_id, store_ids)` → `__init__(self, product_id, company_ids)`
- [ ] `self.store_ids` → `self.company_ids`
- [ ] `product_b__prices__store_id__in=self.store_ids` → `product_b__prices__company_id__in=self.company_ids`
- [ ] Same for the product_a filter

### build_price_slots.py
File: `data_management/utils/cart_optimization/build_price_slots.py`

- [ ] Function signature: `build_price_slots(cart, stores)` → `build_price_slots(cart, companies)`
- [ ] `Price.objects.filter(..., store__in=stores)` → `Price.objects.filter(..., company__in=companies)`
- [ ] `.select_related('store', 'product__brand')` → `.select_related('company', 'product__brand')`
- [ ] `price.store.id` → `price.company_id`
- [ ] `price_obj.store.store_name` → `price_obj.company.name`
- [ ] `company = price_obj.store.company` → `company = price_obj.company`
- [ ] `company_name = price_obj.store.company.name` → `company_name = price_obj.company.name`
- [ ] Remove address construction (`store.address_line_1` etc.) — set `store_address` to `''` or remove from slot dict
- [ ] Update `prices_by_product` keying: `price.store` → `price.company`

### calculate_optimized_cost.py
File: `data_management/utils/cart_optimization/calculate_optimized_cost.py`

- [ ] `all_store_ids` → `all_company_ids`
- [ ] `all_store_names` → `all_company_names`
- [ ] `store_usage` → `company_usage`
- [ ] `option['store_id']` → `option['company_id']`
- [ ] `option['store_name']` → `option['company_name']`
- [ ] Remove `store_to_company` dict (company IS the key now)
- [ ] Remove `store_to_address` / `store_address` (no addresses anymore)
- [ ] Shopping plan: `{name: {'items': [], 'company_name': name}}` (simplified)

### Restore users/utils/cart_optimization.py (file was deleted)
- [ ] Create `users/utils/cart_optimization.py` with `run_cart_optimization(cart_obj, max_stores_options)`:
  - Gets company_ids from `get_default_company_ids()`
  - Gets `Company.objects.filter(id__in=company_ids)`
  - Builds `simple_cart` from `cart_obj.items` (no approved subs)
  - Builds `cart_with_substitutes_slots` (approved subs or original)
  - Calls `build_price_slots`, `calculate_baseline_cost`, `calculate_optimized_cost`, `calculate_best_single_store`
  - No `_translate_shopping_plan` needed (company IS the store now)
  - Returns Response with `baseline_cost`, `optimization_results`, `best_single_store`, `no_subs_results`

### cart_viewset.py
File: `users/views/cart_viewset.py`

- [ ] Add import: `from users.utils.cart_optimization import run_cart_optimization`
- [ ] Add import: `from data_management.utils.cart_optimization.substitute_manager import SubstituteManager`
- [ ] Add import: `from products.utils.default_companies import get_default_company_ids`
- [ ] In `sync` action, after `CartItem.objects.bulk_create(to_create)`, add substitution pre-generation using `get_default_company_ids()` and `SubstituteManager(product_id=..., company_ids=...)`
- [ ] Add `optimize` action (detail=True, POST, url_path='optimize'):
  ```python
  @action(detail=True, methods=['post'], url_path='optimize')
  def optimize(self, request, *args, **kwargs):
      cart_obj = self.get_object()
      max_stores_options = request.data.get('max_stores_options', [2, 3, 4])
      return run_cart_optimization(cart_obj, max_stores_options)
  ```

---

## 9. Update analysis utils (minor)

- [ ] `data_management/analysers/company_analysis.py` — remove Store import and usage; rewrite to query Price directly
- [ ] `data_management/analysers/internal_company_product_crossover.py` — remove Store usage
- [ ] `data_management/utils/analysis_utils/product_overlap/get_product_sets_by_entity.py` — remove Store usage

---

## 10. Update test factories and test files

- [ ] `products/tests/factories/price_factory.py` (or wherever PriceFactory is defined) — change `store = SubFactory(StoreFactory)` → `company = SubFactory(CompanyFactory)`
- [ ] Search for all test files passing `store=` to PriceFactory and change to `company=`:
  ```
  grep -rn "PriceFactory\|store=" products/tests/ companies/tests/ data_management/tests/ users/tests/ --include="*.py"
  ```
- [ ] `products/tests/view_tests/test_product_list_view.py` — update `set_default_stores` to `set_default_companies` using `default_pricing_companies` key (already partially done in a prior session, verify it's consistent)
- [ ] Delete or update any test that tested deleted functionality (store serializers, export-stores view, scheduler, find_stores, etc.) — most of those test files are deleted in Step 1

---

## 11. Migrate

- [ ] `./venv/Scripts/python manage.py makemigrations`
- [ ] If migration is broken or complex: `./venv/Scripts/python manage.py reset_db`
- [ ] `./venv/Scripts/python manage.py migrate`

---

## 12. Run tests and fix

- [ ] `./venv/Scripts/python -m pytest --tb=short -q`
- [ ] Fix any remaining failures

---

## 13. Documentation

- [ ] Create `_docs/deprecated_store.md` — list of all removed files with one-line descriptions
- [ ] Update `_docs/removed_store_grouping.md` — strip code pastes, keep only file paths + brief descriptions

---

## Notes

- Scrapers (ColesScraperV2, ProductScraperWoolworths, ProductScraperAldi) still receive `store_id` as a constructor arg for HTTP API calls — that's fine, it's just not used for DB lookups anymore
- `scraping/utils/coles_session_manager.py` uses store_id for session management — leave as-is
- JSONL file metadata must change `store_id` → `company_name` so UpdateOrchestrator can resolve the Company by name
- The `prices_by_store` cache in UpdateOrchestrator becomes `prices_by_company`
- `nearby_store_ids` disappears from serializer context entirely — serializer just returns all prices
- `store_options` in the old optimization response (multi-store per anchor) is gone — shopping plan keys are now company names directly
