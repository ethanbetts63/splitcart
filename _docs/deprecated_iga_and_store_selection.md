# Removed: IGA Support & Store Selection

IGA was removed because it uses per-store pricing (not national), which required special-casing
throughout the codebase and drove the need for store selection. Store selection was removed because
without IGA all remaining companies (Coles, Woolworths, Aldi) price nationally — no store picker
needed. IGA is also consistently more expensive than Aldi, Coles and Woolworths so the value add
wasn't actually that big for all the complexity.

See git history for all removed code.

---

## IGA — Deleted files

- `scraping/scrapers/product_scraper_iga.py` — IGA product scraper; used a session with retailer store cookie to paginate category/product endpoints
- `scraping/scrapers/store_scraper_iga.py` — IGA store location scraper; scanned salefinder.com.au IDs up to 23001 and parsed HTML store data
- `scraping/utils/product_scraping_utils/DataCleanerIga.py` — cleaned raw IGA product API data; handled TPR/special price logic and sell-by size formatting
- `scraping/utils/product_scraping_utils/get_iga_categories.py` — fetched IGA category hierarchy and extracted leaf categories
- `scraping/utils/shop_scraping_utils/StoreCleanerIga.py` — cleaned raw IGA store API data
- `scraping/tests/util_tests/test_get_iga_categories.py`
- `scraping/tests/util_tests/test_store_cleaner_iga.py`
- `scraping/tests/util_tests/test_data_cleaner_iga.py`

## IGA — Modified files

- `scraping/utils/product_scraping_utils/field_maps.py` — removed `IGA_FIELD_MAP` entry
- `scraping/management/commands/scrape.py` — removed `--iga` argument, IgaScraper import, and elif branch in `_scrape_single_store`
- `scraping/management/commands/find_stores.py` — removed `--iga` argument and `find_iga_stores` call
- `data_management/utils/path_classifier.py` — removed `'iga': 'Iga'` from `_COMPANY_KEY_MAP`
- `products/models/product_price_summary.py` — removed `iga_store_count` field
- `products/utils/bargain_utils.py` — removed IGA two-store bargain special case; simplified to `if len(company_ids) < 2: continue`
- `products/utils/product_ordering.py` — same IGA bargain exception removed
- `products/serializers/product_serializer.py` — removed IGA image resize block
- `data_management/utils/generation_utils/price_summaries_generator.py` — removed `iga_store_count` tracking; simplified company_count guard
- `data_management/utils/generation_utils/bargain_stats_generator.py` — removed IGA average-price logic; all companies now use min price
- `data_management/utils/geospatial_utils.py` — removed IGA never-scraped store exclusion filter
- `data_management/analysers/internal_company_product_crossover.py` — removed IGA Tier 1 start category special case
- `companies/models/store.py` — removed `retailer_store_id` field (IGA-only)
- `scraping/tests/util_tests/test_normalization_e2e.py` — removed IGA cross-check tests
- `products/tests/util_tests/test_bargain_utils.py` — removed IGA two-store bargain test
- `data_management/tests/util_tests/test_geospatial_utils.py` — removed IGA never-scraped exclusion test

---

## Store Selection — Backend deleted files

- `users/models/selected_store_list.py` — SelectedStoreList model: user's named list of Store IDs (M2M), supports both authenticated and anonymous users
- `users/views/selected_store_list_viewset.py` — CRUD viewset for store lists; `active` action returned most-recently-used list
- `users/views/nearby_store_list_view.py` — searched stores near one or more postcodes within a radius, filtered by company
- `users/serializers/selected_store_list_serializer.py` — serializer for SelectedStoreList with stores as PK list
- `users/utils/session_merger.py` — merged anonymous session store list and cart into a newly registered user's account
- `users/utils/cart_optimization.py` — `run_cart_optimization()`: resolved store IDs via `get_pricing_stores_map`, built price slots, ran PuLP optimizer, translated anchor store names back to user-selected stores

## Store Selection — Backend modified files

- `users/models/cart.py` — removed `selected_store_list` FK and its import
- `users/views/cart_viewset.py` — removed: store list association in `perform_create`, lazy-link in `active`, lazy-link in `sync`, substitute pre-generation gated on store list, entire `optimize` action
- `users/urls.py` — removed `store-lists` router registration, `stores/nearby/` URL, and related imports

---

## Store Selection — Frontend deleted files

- `frontend/src/context/StoreListContext.tsx` — React context managing the active store list: fetching, saving, creating, deleting, and toggling individual stores
- `frontend/src/context/StoreSearchContext.tsx` — React context managing nearby-store search state: postcode, radius, company filter, map bounds, search handler
- `frontend/src/services/storeList.api.ts` — API calls for store list CRUD (fetch active, list, load, save, create, delete)
- `frontend/src/services/store.api.ts` — API call to search nearby stores by postcode/radius/companies
- `frontend/src/components/NavLocationButton.tsx` — nav bar pin icon showing selected store count badge
- `frontend/src/components/StoreList.tsx` — checkbox list of stores with company logo
- `frontend/src/components/StoreMap.tsx` — Leaflet map showing store markers with company logo icons
- `frontend/src/page_components/dialog-pages/EditLocationPage.tsx` — full store picker dialog: postcode input, radius slider, company filter, store list, map
- `frontend/src/types/SelectedStoreListType.ts`
- `frontend/src/types/ActiveStoreListData.ts`
- `frontend/src/types/StoreListContextType.ts`
- `frontend/src/types/StoreSearchContextType.ts`
- `frontend/src/types/StoreListProps.ts`
- `frontend/src/types/StoreMapProps.ts`
- `frontend/src/types/EditLocationPageProps.ts`
- `frontend/src/types/SearchParams.ts`
- `frontend/src/types/NearbyStoresResponse.ts`

## Store Selection — Frontend modified files

- `frontend/src/app/providers.tsx` — removed `StoreListProvider` and `StoreSearchProvider` wrappers
- `frontend/src/components/settings-dialog.tsx` — removed "Edit Location" nav item, `EditLocationPage` case, all local store selection state and `useStoreList` usage
- `frontend/src/types/index.ts` — removed re-exports for all deleted store selection types
- `frontend/src/types/Cart.ts` — removed `selected_store_list` field and its import
