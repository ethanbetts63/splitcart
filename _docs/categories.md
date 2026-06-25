# Category System Overview

The SplitCart category system normalises messy, store-specific product data into a clean browsing experience. It has three tiers: raw Categories → Primary Categories → Pillar Pages.

---

## 1. Raw Categories

**What they are:** The category hierarchy scraped directly from each supermarket's website. Every product on Woolworths, Coles, Aldi, and IGA belongs to a chain of categories (e.g. `Health & Beauty → Personal Care → Hair Care → Hair Colour`). These are stored as `Category` model objects in `companies/models/category.py`.

**How they get into the database:** During scraping, each product comes with a `category_path` — an ordered list of category names from root to leaf (e.g. `["Health & Beauty", "Personal Care", "Hair Care", "Hair Colour"]`). The `CategoryManager` (in `data_management/database_updating_classes/product_updating/category_manager.py`) does three things with this:

1. Creates a `Category` object for each node in the path that doesn't already exist.
2. Creates parent-child links between adjacent nodes in the path (so "Hair Care" knows its parent is "Personal Care").
3. Links the product to its **leaf** category (the last item in the path — "Hair Colour" in the example above).

**Woolworths note:** Woolworths now uses the canonical path from the category-tree scrape work item. The old merge of `piesdepartmentnamesjson`, `piescategorynamesjson`, and `piessubcategorynamesjson` was removed because those fields include merchandising facets like Dinner, Breakfast, and Lunch Box, not just taxonomy. Existing bad category rows are expected to disappear on the next DB reset/rebuild.

**Coles note:** Coles `onlineHeirs` paths are ordered, but products can appear under normal, seasonal, and promotional hierarchies. The current cleaner uses the first `onlineHeirs` entry, so paths such as Christmas, Down Down, and Bonus Credit Products can override the real grocery taxonomy. Prefer non-promotional grocery paths, ideally matched to the browse category context.

**Aldi/IGA note:** Aldi and IGA already fetch category trees but currently keep only leaf identifiers for scraping. Aldi product category paths are mostly coherent, but seasonal/merchandising roots such as Christmas, Limited Time Only, and Front Of Store appear in the data. IGA paths are the cleanest observed: they consistently sit under Grocery with low multi-path ambiguity. Both would still be safer if their scrape work items carried full category paths, matching the Woolworths approach.

---

## Proposed Path-Aware Refactor

The current `Category` model stores one node per `(slug, company)` and links products to the leaf node. That loses the full path identity. It also cannot represent the important fact that the same product can be found under multiple full paths within the same company.

Preferred replacement: store full category paths directly on `Product`, modelled after `normalized_name_brand_size_variations`.

```text
Product
  category_paths = [
    {
      "company": "Coles",
      "path": ["Dairy, Eggs & Fridge", "Milk", "Full Cream Milk"],
      "path_type": "canonical_taxonomy",
      "canonical_key": "dairy/milk/full-cream",
      "primary_category_slug": "milk"
    },
    ...
  ]
  primary_category_slugs = ["milk", "dairy"]
```

This keeps the design closer to the product-name variation system: collect observed variants, normalize/canonicalize them, and store the generated result on the product. The tradeoff is queryability: product filtering and stats will need JSON-aware querying or generated helper fields/indexes. If that becomes painful, the same shape can later be promoted into a separate path table.

Each `category_paths` entry must carry `company`. `Product` is canonical across companies, so a category path without company context is ambiguous and unsafe.

The product should keep two category outputs:

1. `category_paths` — detailed evidence and canonicalization data for each observed company/path.
2. `primary_category_slugs` — a small denormalized list used for fast browsing, filtering, stats, and frontend category pages.

Suggested product field shape:

```python
Product.category_paths = [
  {
    "company": "Woolworths",
    "path": ["Dairy, Eggs & Fridge", "Yoghurt", "Kefir"],
    "path_key": "woolworths|dairy-eggs-fridge/yoghurt/kefir",
    "root_name": "Dairy, Eggs & Fridge",
    "leaf_name": "Kefir",
    "path_type": "canonical_taxonomy",
    "canonical_key": "dairy/yoghurt/kefir",
    "primary_category_slug": "yogurt",
    "evidence_count": 12,
  }
]
```

This means the current `Category` model can probably be retired. `PrimaryCategory` should stay as the public browsing layer. `CategoryLink` should be replaced by generated path-aware canonical category mappings, not linked raw node IDs.

### Downstream Category Pipeline

1. Collect every unique full category path seen for a product/company.
2. Classify each path:
   - `canonical_taxonomy`
   - `dietary`
   - `seasonal`
   - `promotion`
   - `brand_collection`
   - `merchandising`
   - `unknown`
3. Generate a path-aware canonical category mapping:

```python
"coles|Dairy, Eggs & Fridge/Milk/Full Cream Milk": "dairy/milk/full-cream"
"woolworths|Dairy, Eggs & Fridge/Milk/Full Cream Milk": "dairy/milk/full-cream"
"iga|Grocery/Dairy, Eggs And Fridge/Milk And Cream/Full Cream Milk": "dairy/milk/full-cream"
```

4. Write the generated mapping to `data_management/data/category_path_mappings.py` or an equivalent generated JSONL artifact. It should include raw company path, path type, canonical key, primary category slug, confidence, and source/reason.
5. Assign `primary_category_slugs` from canonical category keys, not from raw leaf node names.
6. Generate substitutions from canonical category assignments:
   - LVL3 equivalent: products sharing the same canonical category.
   - LVL4 equivalent: products in related canonical categories.

The downstream system should mostly consume canonical outputs, not raw path types directly. Non-canonical paths can stay in `category_paths` as evidence, but product browsing, stats, and substitutions should use `primary_category_slugs` / canonical category keys. The generated mapping should be inspectable and reproducible, similar to product name translation tables. It can start with deterministic rules and embedding similarity, then use an AI pipeline for ambiguous path-level decisions.

### Refactor TODO

- [ ] Scrapers: make every company emit full scrape-context paths where possible. Woolworths already does this. Coles should prefer a menu/browse-context full path over `onlineHeirs[0]`. Aldi and IGA category-tree helpers should keep full paths instead of leaf identifiers only.
- [ ] Cleaners: allow `category_paths` as a list of full paths, not only one `category_path`. Product metadata paths can remain as fallback/debug evidence but should not blindly override scrape-context paths.
- [ ] Product ingest: replace `CategoryManager` with product-level path aggregation. It should merge evidence for the same product/company/path into `Product.category_paths` instead of creating node graphs.
- [ ] Models: add `Product.category_paths` as a JSON field, similar in spirit to `normalized_name_brand_size_variations`. Add `Product.primary_category_slugs` as the fast downstream/filtering field.
- [ ] Primary categories: replace `CATEGORY_MAPPINGS` from raw category-name mapping with path/canonical-key mapping. `PrimaryCategoriesGenerator` should write canonical keys / primary category slugs into product category path entries, not node descendants.
- [ ] Category path mappings: create `data_management/data/category_path_mappings.py` or equivalent generated JSONL artifact to store path type, canonical key, primary category slug, confidence, and reason/source.
- [ ] Category links: remove `CategoryLink` as raw node-to-node matching. Replace with generated canonical category mappings and related-canonical-category edges.
- [ ] Substitutions: update `ProductExportSerializer`, `SubstitutionsGenerator`, `Lvl3SubGenerator`, and `Lvl4SubGenerator` to consume canonical category IDs/keys instead of `Product.category` raw node IDs.
- [ ] Product list filtering: replace queries like `category__primary_category__slug__in` with filtering over `Product.category_paths`. If JSON querying is too slow, add a denormalized/indexed helper field such as `primary_category_slugs`.
- [ ] Bargain/category ordering: update `products/utils/product_ordering.py`, `companies/management/commands/category_stats.py`, and `price_comparisons_generator.py` to use primary categories assigned through paths.
- [ ] API exports: replace `/api/export/categories/`, `/api/export/categories-with-products/`, and `/api/export/category_links/` with path/canonical-category exports.
- [ ] Serializers/frontend: keep `PrimaryCategory` output stable for the frontend, but update product serialization/prefetches that currently expect `category__primary_category`.
- [ ] Cleanup: remove `CategoryCycleManager`, parent/child category graph traversal, category exclusions tied to node names, old category-link upload/update flows, and raw node review commands if they no longer apply.
- [ ] Tests: rewrite category manager tests around full path identity, multi-path product assignment, path classification, primary category assignment, and substitution grouping.

### Current Code Touchpoints

- Models:
  - `companies/models/category.py` — raw node model to replace.
  - `companies/models/category_link.py` — raw category link model to replace.
  - `products/models/product.py` — `Product.category` M2M currently points to raw `Category`.
  - `companies/models/primary_category.py` — should stay, but product membership should come from `Product.category_paths` or a denormalized helper field.
- Ingest:
  - `data_management/database_updating_classes/product_updating/category_manager.py` — creates raw nodes, parent links, and product-leaf links. This becomes the path ingest manager.
  - `data_management/database_updating_classes/product_updating/update_orchestrator.py` — builds category cache, calls `CategoryManager`, and runs `CategoryCycleManager`.
  - `data_management/database_updating_classes/product_updating/post_processing/category_cycle_manager.py` — should disappear with node graph removal.
- Scraping:
  - `scraping/utils/product_scraping_utils/get_woolworths_categories.py` and `scraping/scrapers/product_scraper_woolworths.py` — already moving toward scrape-context paths.
  - `scraping/utils/product_scraping_utils/get_coles_categories.py`, `get_store_specific_categories_coles.py`, `product_scraper_coles_v2.py`, `product_scraper_coles_v3.py`, `DataCleanerColes.py` — need path-aware Coles work items and non-promotional path selection.
  - `get_aldi_categories.py`, `product_scraper_aldi.py`, `DataCleanerAldi.py` — need full path work items.
  - `get_iga_categories.py`, `product_scraper_iga.py`, `DataCleanerIga.py` — need full path work items.
- Primary category generation:
  - `data_management/data/category_mappings.py` — should move from raw name mapping to path/canonical-key mapping.
  - `data_management/data/category_exclusions.py` — likely replaced by path classification rules.
  - `data_management/utils/generation_utils/primary_categories_generator.py` — currently traverses raw category descendants.
- Category-link generation and upload:
  - `data_management/utils/generation_utils/category_links_generator.py`
  - `data_management/database_updating_classes/category_link_update_orchestrator.py`
  - `scraping/utils/command_utils/category_links_uploader.py`
  - `products/views/export_category_links_view.py`
- Substitution generation:
  - `products/serializers/product_export_serializer.py` exports raw category IDs.
  - `companies/serializers/category_export_serializer.py` and `category_with_products_export_serializer.py` export raw categories.
  - `data_management/utils/generation_utils/substitutions_generator.py`
  - `data_management/utils/substitution_generators/lvl3_sub_generator.py`
  - `data_management/utils/substitution_generators/lvl4_sub_generator.py`
- Product browsing and stats:
  - `products/views/product_list_view.py`
  - `products/utils/product_ordering.py`
  - `products/views/bargain_carousel_view.py`
  - `data_management/utils/generation_utils/price_comparisons_generator.py`
  - `companies/management/commands/category_stats.py`
  - `companies/management/commands/primary_cat_stats.py`

**Important: categories are unique by `(slug, company)`.** If the same category name appears in two different paths — e.g. `["Baby & Toddler", "Health"]` and `["Health & Beauty", "Health"]` — there is only ONE `Category` object for "Health" for that company, and it ends up with two parents. This is a known design limitation; see the Known Issues section below.

**Key fields on `Category`:**
- `name` — the raw name from the store's website (title-cased on ingest via `_clean_category_path`)
- `company` — which supermarket this belongs to
- `parents` — M2M self-reference to parent categories
- `subcategories` — reverse of `parents` (the children)
- `primary_category` — FK to the assigned `PrimaryCategory` (set by the generator, not the scraper)

---

## 2. Primary Categories

**What they are:** Standardised, cross-company categories. Where each supermarket has its own names and hierarchy, Primary Categories give a single consistent label. The `PrimaryCategory` model lives in `companies/models/primary_category.py`.

**How the mapping is defined:** `data_management/data/category_mappings.py` contains `CATEGORY_MAPPINGS` — a dict keyed by company name, then by raw category name, pointing to the primary category name to assign. `None` means "exclude this category entirely".

```python
CATEGORY_MAPPINGS = {
    'Woolworths': {
        'Hair Care': 'Beauty',
        'Baby': 'Baby',
        'Frozen': 'Freezer',
        ...
    },
    'Coles': { ... },
    ...
}
```

The same file also contains `PRIMARY_CATEGORY_HIERARCHY` — a dict that defines parent-child relationships *between* primary categories (e.g. `"Dairy": ["Cheese", "Milk", "Yogurt"]`). This is used by the `ProductListView` to include sub-categories when filtering: browsing "Dairy" also shows Cheese, Milk, and Yogurt products.

**How the generator works (`PrimaryCategoriesGenerator`):**

Run via `python manage.py generate --primary-cats`. It:

1. Deletes all existing `PrimaryCategory` objects (this cascades to set `primary_category=null` on all raw `Category` objects via `SET_NULL`).
2. Re-creates `PrimaryCategory` objects from all unique values in `CATEGORY_MAPPINGS`.
3. Sets up the `PRIMARY_CATEGORY_HIERARCHY` sub-category links.
4. Assigns each raw `Category` its primary category via `_assign_primary_categories`:
   - For each mapping entry, finds all `Category` objects matching that name and company.
   - Assigns the primary category to the matched category **and all of its descendants** (via `_get_all_descendants`). This means you don't have to list every leaf subcategory — mapping a parent covers its whole subtree.
   - The traversal **stops** at any child that has its own explicit entry in `CATEGORY_MAPPINGS`. That child's own mapping handles its subtree. This prevents cross-hierarchy contamination (see Known Issues).
   - `category_exclusions.py` provides an additional fine-grained exclusion list for edge cases.

**Usage:** Primary categories power the category filter bar and the `?primary_category_slug=` filter on the product list endpoint.

---

## 3. Pillar Pages

**What they are:** High-level landing pages that group multiple primary categories together. Designed for the homepage navigation and SEO. The `PillarPage` model lives in `companies/models/pillar_page.py`.

**How they are defined:** `data_management/data/pillar_pages.jsonl` — one JSON object per line, each specifying a slug, name, hero copy, and a list of `primary_category_slugs` to include.

**How the generator works (`PillarsGenerator`):** Run via `python manage.py generate --pillars`. Reads the JSONL file and creates `PillarPage` objects linked to the specified `PrimaryCategory` objects.

**Usage:** Used in the "Browse Categories" section on the homepage.

---

## Category Links

`generate --cat-links` creates cross-company raw category links used by LVL4 substitutions. It now only emits `MATCH` links from semantic category-name similarity; the old product-overlap `CLOSE`/`DISTANT` path was removed because it produced almost no links and added complexity without useful signal.

---

## Data Flow Summary

```
Scraper
  └─ product has category_path: ["Health & Beauty", "Personal Care", "Hair Colour"]
       │
       ▼
CategoryManager (runs on every product ingest)
  ├─ Creates Category objects for each node (unique by slug + company)
  ├─ Creates parent → child links between adjacent nodes
  └─ Links product to its leaf Category ("Hair Colour")
       │
       ▼
PrimaryCategoriesGenerator (run manually: generate --primary-cats)
  ├─ Reads CATEGORY_MAPPINGS
  ├─ Assigns primary_category to each raw Category + its unmapped descendants
  └─ "Hair Colour" → Beauty  (because 'Hair Care': 'Beauty' is in the mapping
                               and traversal covers Hair Care's children)
       │
       ▼
PillarsGenerator (run manually: generate --pillars)
  └─ Groups primary categories into PillarPage objects
       │
       ▼
Frontend
  ├─ Category bar → lists PrimaryCategory objects
  ├─ Homepage → links to PillarPage objects
  └─ Product list → filters by primary_category__slug
```

---

## Known Issues / Design Limitations

**Category name collisions.** Because categories are unique by `(slug, company)`, the same name appearing in two different scraper paths produces one Category object with two parents. This makes that node reachable from both hierarchy branches. Before the fix in `_get_all_descendants`, a traversal from "Baby & Toddler" could reach "Hair Colour" via a shared intermediate node and incorrectly assign it to the Baby primary category.

The traversal boundary fix mitigates this: traversal stops at any child that has its own explicit mapping entry. This prevents contamination in the vast majority of cases, but unmapped descendants of a collided node can still inherit the wrong primary category if neither of their ancestor chains has an explicit boundary in the mapping file. The correct long-term fix would be path-aware category uniqueness (store categories by full path, not just name).

**Mapping file maintenance.** `CATEGORY_MAPPINGS` is maintained manually. New categories added by supermarkets during scraping will silently have no primary category until the file is updated. The generator logs a warning for any mapping entry whose category name isn't found in the database, but it does not warn about categories in the database that have no mapping.

---

## Implementation Plan

Fresh DB assumed — no backfill needed. No feature flags. Phases are sequential; check off as done. Note dead code and issues inline.

### Phase 1 — Add new fields to Product (non-destructive)
- [x] Add `Product.category_paths` JSONField (default list) — stores full per-company path evidence
- [x] Add `Product.primary_category_slugs` JSONField (default list) — fast denormalized filter field
- [x] Create and run migration

### Phase 2 — Scraper path improvements
- [x] **Woolworths** — already emits full scrape-context paths, no change needed
- [x] **Coles** — `DataCleanerColes._pick_canonical_heir`: scans all `onlineHeirs`, picks first non-promotional root; falls back to `[0]` if all promotional. Promotional roots: christmas, down down, bonus credit products, specials, front of store, seasonal, everyday market, big night in.
- [x] **Aldi** — `get_aldi_categories._find_leaf_categories`: skips subtrees whose root name is in `_ALDI_PROMOTIONAL_ROOTS`; returns same `(urlSlugText, key)` tuples for backward compat
- [x] **IGA** — `get_iga_categories._find_leaf_categories`: skips promotional root subtrees; IGA paths are cleanest so minimal real-world impact

### Phase 3 — PathManager replaces CategoryManager
- [x] Write `PathManager` (`path_manager.py`) — merges incoming paths into `Product.category_paths` (no node creation, no parent links); increments `evidence_count` on re-seen paths
- [x] Wire `PathManager` into `update_orchestrator.py` (replaced `CategoryManager` call; removed `Category` cache build)
- [x] Removed `CategoryCycleManager` from post-processing in orchestrator
- [x] Removed `Category` and `CategoryCycleManager` imports from orchestrator
- [ ] Keep `Category` M2M on Product temporarily — remove in Phase 8

### Phase 4 — Path classifier + canonical key mapping
- [x] Inspected real path data across all four companies (sampled JSONL files)
- [x] `data_management/utils/path_classifier.py` — `classify_path(company, path)` returns `path_type`, `canonical_key`, `primary_category_slug`. Path type classified from root node against frozensets (seasonal, promotional, dietary, brand_collection, merchandising, canonical_taxonomy). `primary_category_slug` derived by scanning path leaf→root through existing `CATEGORY_MAPPINGS`.
- [x] Classification wired into `PathManager` — happens at ingest time, no separate generation step needed
- [x] `CATEGORY_MAPPINGS` is REUSED (not replaced) as the lookup source for `primary_category_slug` — the classifier wraps it path-aware
- [x] `category_exclusions.py` is SUPERSEDED by path classification rules (promotional/seasonal paths never get a primary category slug) — kept as file for now, removed in Phase 8

### Phase 5 — PrimaryCategoriesGenerator refactor
- [x] Rewrote `PrimaryCategoriesGenerator` — reads `Product.category_paths` to populate `Product.primary_category_slugs`; no graph traversal
- [x] Kept `PrimaryCategory` model, `_create_primary_categories`, `_assign_sub_categories`, `PRIMARY_CATEGORY_HIERARCHY` — same as before
- [x] Removed `_assign_primary_categories` graph traversal and `_get_all_descendants`
- [x] `_populate_product_primary_category_slugs`: collects slugs from canonical_taxonomy paths first; falls back to dietary, then any path, if empty

### Phase 6 — Substitutions + stats update
- [x] Update `SubstitutionsGenerator` — removed `categories` and `category_links` API fetches; only fetches products now
- [x] Update `Lvl3SubGenerator` — groups products by each `primary_category_slug` from `p.get('primary_category_slugs', [])`; encodes all unique products once and reuses embeddings
- [x] Update `Lvl4SubGenerator` — replaced `CategoryLink` connected-components with `PRIMARY_CATEGORY_HIERARCHY` super-groups; slug dedup prevents Lvl4 for same-primary-category pairs (those are Lvl3)
- [x] Update `price_comparisons_generator.py` — switched from `product__category__primary_category_id` grouping to `Product.primary_category_slugs`; Python-level grouping per slug
- [x] Update `product_ordering.py` — replaced `product__category__primary_category__slug__in` with `_primary_category_slug_filter()` (JSON contains OR per slug)
- [x] Update `category_stats.py` — switched to `primary_category_slugs__contains=[slug]` filter
- [x] Update `primary_cat_stats.py` — rewrote to report product counts per PrimaryCategory via `primary_category_slugs` instead of raw Category counts

### Phase 7 — API filtering switch
- [x] Update `ProductListView` — replaced `category__primary_category__slug__in` with `_primary_category_slug_filter()`; removed all `category__primary_category` prefetches (3 occurrences)
- [x] Update `ProductExportSerializer` — replaced `category` (raw M2M PKs) with `primary_category_slugs` JSONField
- [x] Update `bargain_carousel_view.py` — removed `category__primary_category` from prefetch_related
- [ ] Update API export endpoints — replace `/api/export/categories/`, `/api/export/categories-with-products/`, `/api/export/category_links/` with path/canonical-category exports (deferred to Phase 8)
- [x] Frontend `?primary_category_slug=` parameter unchanged — API surface stable

### Phase 8 — Cleanup
- [ ] Remove `Category` model (`companies/models/category.py`) + migration
- [ ] Remove `CategoryLink` model (`companies/models/category_link.py`) + migration
- [ ] Remove `Product.category` M2M field + migration
- [ ] Remove `CategoryManager` (`data_management/database_updating_classes/product_updating/category_manager.py`)
- [ ] Remove `CategoryCycleManager` (`post_processing/category_cycle_manager.py`)
- [ ] Remove `category_links_generator.py`, `category_link_update_orchestrator.py`, `category_links_uploader.py`
- [ ] Remove old API export views for raw categories/links
- [ ] Remove `CATEGORY_MAPPINGS` / `category_exclusions.py`
- [ ] Run full test suite; rewrite category-related tests around path identity

### Issues / Dead Code Noted
- `category_exclusions.py` is a parallel exclusion list alongside `CATEGORY_MAPPINGS` — likely redundant even now; worth auditing before Phase 4
- Coles `onlineHeirs[0]` selection is the biggest correctness risk — Christmas/promotional paths can silently override real taxonomy
- `CategoryCycleManager` exists because the node graph can produce cycles; it disappears entirely with the path model
- `PRIMARY_CATEGORY_HIERARCHY` in `category_mappings.py` (parent-child between primary cats) is separate from the raw Category graph and should survive into the new system
- MySQL `JSON_CONTAINS` on `primary_category_slugs` — keep an eye on query performance at scale; a junction table is the escape hatch if needed
- `users/views/cart_viewset.py` lines 256/259 still prefetch `items__product__category__primary_category` — dead weight now, remove in Phase 8
- Old export endpoints `ExportCategoriesView` / `ExportCategoriesWithProductsView` / `ExportCategoryLinksView` still exist and are referenced in `products/urls.py` — remove in Phase 8
