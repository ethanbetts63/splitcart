# SplitCart Recommendations

A living to-do list of approved improvements. Items are grouped by area and ordered roughly by priority within each group.

---
---
# Concepts that need documentation

 ProductBrand model — The brand system is more complex than it looks. It has confirmed_official_prefix, longest_inferred_prefix, name_variations,
  normalized_name_variations, and the whole reconciliation logic. It touches GS1, the nnbs system, and the translation tables. There's no doc for it
   and it's central to everything.



## UX — Substitution Flow

- [ ] **Jumpable step indicator** — Currently the only way to go back to a previous substitution item is to click Back repeatedly. Add a clickable step indicator (dots or numbered pills) above the progress bar so users can jump directly to any item they've already seen.

- [ ] **"Review all" list view** — The step-by-step flow is clear for small carts but tedious for large ones. Consider a toggle between the current "one at a time" mode and an "all at once" list view where every item and its substitutes are visible on a single scrollable page. Power users would prefer this.

- [ ] **Running cart summary during substitution** — While working through substitutions the user has no reminder of their full list. A small collapsed header or sidebar showing "12 items in cart · 4 substitutions approved" would provide useful context without taking up space.

- ** progress bar ** this would be easy to implemnt and we could steal it from futureflower. 

---

## UX — Results Page

- [ ] **Explicit "Recommended" label** — The highest-saving tab gets a green badge but users still have to interpret it. Add a clear "Recommended" label to the best-saving tab to remove ambiguity.

- [ ] **Show percentage saving in the panel header** — The savings amount is shown in the tab badge and in the panel as a dollar figure, but the percentage isn't visible inside the panel itself. Showing "You saved 14%" prominently alongside the dollar saving in the panel header would be more satisfying and instantly legible.

---

## Security

*(To be discussed)*

---

## Complexity / Architecture

### Store List & Cart

- [ ] **`last_used_at` on `SelectedStoreList` is semantically wrong** — The field uses `auto_now_add`, so it's set once at creation and never updated. It's effectively `created_at`. The `sync` view and `active` endpoint both order by `-last_used_at` to find the "most recently used" list, but they're actually getting the most recently *created* one. For single-list users this doesn't matter. For authenticated multi-list users it silently uses the wrong list. Fix: either rename to `created_at` to be honest, or change to `auto_now` to track last modification. **File:** `users/models/selected_store_list.py`.

- [ ] **`isCartSyncing` not set during substitution approvals** — `addItem` and `updateItemQuantity` both set `isCartSyncing = true` before calling `debouncedSync`. `updateCartItemSubstitution` calls `debouncedSync` but never sets the flag. No visible UX consequence right now, but inconsistent and could cause subtle bugs if anything guards on that flag in future. **File:** `frontend/src/context/CartContext.tsx`.

- [ ] **`ProductSubstituteListView` cache is now much less effective** — The endpoint has a 6-hour `cache_page`. Before store filtering was added it cached one entry per product. Now the cache key includes 15+ store IDs, making the hit rate much lower. Consider replacing with a tighter cache on just the unfiltered substitution lookup, or relying on React Query's client-side cache instead. **File:** `products/views/product_substitute_list_view.py`.

---

### Category System

**Issue 1 — Products appearing in wrong primary categories**

Two sub-causes:

**A. Cross-hierarchy contamination via shared category nodes.** Categories are stored uniquely by `(slug, company)`, not by full path. If the same category name appears in two different hierarchy paths (e.g., "Health" under both "Baby & Toddler" and "Health & Beauty"), there is ONE database object with two parents. `PrimaryCategoriesGenerator._get_all_descendants` then traverses the entire subtree of a matched category. When traversal crosses into the wrong parent's branch via a shared node, products from unrelated categories get assigned the wrong primary category (e.g., hair colour products appear on the baby page).

**Proposed fix:** Modify `_get_all_descendants` to stop recursing when it encounters a category whose name has its own explicit entry in the `CATEGORY_MAPPINGS` dict for that company. Parent traversals cover only unmapped gaps; explicitly-mapped categories handle their own subtrees. Small change to the generator.

**B. Incorrect entries in `category_mappings.py`.** Several Woolworths mappings are clearly wrong:
- `'Antipasto': 'Non-Alcoholic Drinks'` → should be `'Miscellaneous'` or `None`
- `'Asian Ready Meals': 'Non-Alcoholic Drinks'` → should be `'International'` or `'Deli'`
- `'Board Games & Puzzles': 'Non-Alcoholic Drinks'` → should be `None`

These need a manual audit pass of the full mapping file to catch others like them.

---


  6. get_store_specific_categories_coles.py — A GraphQL-based dynamic category fetcher. Has no .pyc, is never imported. The dynamic approach was
  written but never wired in. Meanwhile get_coles_categories.py has a TODO: Implement a more robust way comment. These two files exist in a stalled
  state — the solution exists but was never connected. hardcoding the categories is an issue. but scraping coles is quite tricky. grabbing the categories will need checking even if we arleady have logic for it i dont know if it works. 

   20. IGA company name lowercase mismatch (scrape_barcodes.py:25 vs rest of pipeline)
  ColesBarcodeScraperV2 hardcodes self.company = "coles" (lowercase). Every other path gets the company name from store.company.name in the DB (e.g.
   "Coles" with capital). PriceNormalizer does self.company.lower() == 'aldi', so the case doesn't matter there. But metadata written to JSONL files
   from the barcode scraper would have "coles" lowercase while regular scrapes write "Coles". The ingestion pipeline may be case-insensitive enough
  that this doesn't break anything, but it's inconsistent.



## Notes

- Product pages (individual products) are intentionally excluded from the sitemap. With hundreds of thousands of products, indexing them all would waste crawl budget and the pages themselves have thin content (name + price). Not worth pursuing.
- The `PriceComparisonChart` component already renders text summaries ("X% of Fruit tested were cheaper at Woolworths than Coles") in plain HTML — Google can read these. No changes needed there.

    ---
  2. SchedulerView does a write inside a GET

  store.save(update_fields=['needs_rescraping', 'scheduled_at'])

  GET requests are supposed to be idempotent — no side effects. HTTP clients retry GETs. Load balancers replay them. You saw this bite you directly
  in the tests (required transaction=True).

  It should be a POST. The scraper asks "give me the next store" and confirms it received it — that's a state change, which is what POST is for.



  - The 1ea → ea normalization in _get_standardized_sizes is a one-liner special case that suggests the regex patterns upstream aren't handling the
  1× multipack correctly. Worth a unit test for "1ea" → "ea" to pin the behaviour.

  ProductEnricher.enrich_canonical_product() mutates the passed canonical_product object in-place, then returns a boolean. ProductManager uses the
  boolean to decide whether to add it to the bulk_update list. If an exception is thrown between enrich and bulk_update, the in-memory object is
  dirty but the DB is unchanged. In normal operation this is harmless because the whole run restarts. But it's a fragility worth knowing about.

  1. IGA name check is wrong in BargainStatsGenerator

  bargain_stats_generator.py:32 checks if name == 'Iga': — titlecase. Every other IGA check in the codebase uses .lower() == 'iga'. If the company
  is stored as 'IGA' (which is likely given title-casing conventions elsewhere), this condition never fires. IGA prices would be treated as min()
  instead of avg(), which is wrong for store-by-store pricing. This is a silent logic error — no exception, just incorrect stats.

  2. percent_same can go negative or exceed 100

  bargain_stats_generator.py:78:
  percent_same = 100 - percent_a - percent_b
  Both percent_a and percent_b are independently rounded. If the true split is 50.4% / 49.6% / 0%, rounding gives 50 + 50 = 100, so percent_same = 0
   — fine. But if it's 50.6% / 50.6% / ~-1.2%, you get percent_same = -1. The result is stored directly in JSON and served to the frontend. Should
  round the raw float for same_price and derive the percentages from the raw counts, not by subtraction.

  1. Hardcoded division IDs in get_nearby_stores
  excluded_division_ids = [2, 3, 5, 7]
  These are raw DB PKs. If the DB is ever reset or re-seeded those IDs will be wrong silently. Worth filtering by division name instead.

  2. print() calls in build_price_slots
  The rest of the codebase passes command through for logging. build_price_slots uses bare print() — these won't show up in any log aggregation and
  can't be suppressed in tests.

  3. calculate_best_single_store has an unfinished savings calculation
  'savings': 0,  # Savings calculation is complex here, maybe compare to baseline?
  This field is in the response contract but is always 0. Worth either wiring it up or removing it from the return value so callers aren't misled.

  4. get_nearby_postcodes and get_nearby_stores load everything into Python
  Both fetch every postcode/store from the DB and filter in Python with the Haversine formula. Fine for current scale, but there's no bounding box
  pre-filter. As the dataset grows this will get slow — a simple lat/lon bounding box WHERE clause before the Python loop would cut down the set
  significantly.

  5. Two map_generator.py files
  utils/analysis_utils/map_generator.py
  utils/generation_utils/map_generator.py
  One of these is likely dead code or a forgotten duplicate. Worth checking which is actually imported anywhere.

  6. CategoryCycleManager prefetch that doesn't fully help
  prefetch_related('parents') is called on the initial queryset, but inside _prune_cycles_recursive there are further current_node.parents.all()
  calls on nodes that weren't in that initial queryset (they're travers