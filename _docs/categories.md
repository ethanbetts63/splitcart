# Category System Overview

The SplitCart category system normalises messy, store-specific product data into a clean browsing experience. It has three tiers: raw Categories → Primary Categories → Pillar Pages.

---

## 1. Raw Categories

**What they are:** The category hierarchy scraped directly from each supermarket's website. Every product on Woolworths, Coles, Aldi, and IGA belongs to a chain of categories (e.g. `Health & Beauty → Personal Care → Hair Care → Hair Colour`). These are stored as `Category` model objects in `companies/models/category.py`.

**How they get into the database:** During scraping, each product comes with a `category_path` — an ordered list of category names from root to leaf (e.g. `["Health & Beauty", "Personal Care", "Hair Care", "Hair Colour"]`). The `CategoryManager` (in `data_management/database_updating_classes/product_updating/category_manager.py`) does three things with this:

1. Creates a `Category` object for each node in the path that doesn't already exist.
2. Creates parent-child links between adjacent nodes in the path (so "Hair Care" knows its parent is "Personal Care").
3. Links the product to its **leaf** category (the last item in the path — "Hair Colour" in the example above).

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
