# Category System

The category system converts messy, company-specific product hierarchies into a consistent cross-company browsing layer. It works in three stages: path ingest → primary category assignment → cross-company canonical matching.

---

## Models

**`PrimaryCategory`** — the public browsing layer. Cross-company, human-readable category labels (Milk, Cheese, Yogurt, etc.). Lives in `companies/models/primary_category.py`. These are what the frontend filters on.

**`PillarPage`** — groups multiple primary categories into SEO landing pages (e.g. "Dairy" groups Milk, Cheese, Yogurt). Lives in `companies/models/pillar_page.py`, defined in `data_management/data/pillar_pages.jsonl`.

The old raw `Category` node-graph model and `CategoryLink` model are being phased out (Phase 8 cleanup). Primary category assignment now comes entirely from `Product.category_paths`.

---

## Product fields

Each `Product` carries two category fields:

**`category_paths`** — a JSON list of every category path seen for this product, per company. Each entry:
```python
{
    "company": "Woolworths",
    "path": ["Dairy, Eggs & Fridge", "Yoghurt", "Greek Yoghurt"],
    "path_key": "woolworths|dairy-eggs-fridge/yoghurt/greek-yoghurt",
    "root_name": "Dairy, Eggs & Fridge",
    "leaf_name": "Greek Yoghurt",
    "path_type": "canonical_taxonomy",
    "canonical_key": "dairy-eggs-fridge/yoghurt/greek-yoghurt",
    "primary_category_slug": "yogurt",
    "evidence_count": 14,
}
```

**`primary_category_slugs`** — a small denormalized JSON list of PrimaryCategory slugs derived from `category_paths`. Used for all product filtering, stats, and substitution grouping. Example: `["yogurt", "dairy"]`.

---

## Path ingest — PathManager

`data_management/database_updating_classes/product_updating/path_manager.py`

Runs during `update --products` (via `UpdateOrchestrator`). Replaces the old `CategoryManager`. For each incoming product with a `category_path`:

1. Computes `path_key = "{company}|{slugified/path}"`.
2. Looks up the product's existing `category_paths`.
3. If the path_key is already present, increments `evidence_count`.
4. If new, calls `classify_path()` and appends a new entry.
5. Batch-updates `Product.category_paths` via `bulk_update`.

No `Category` objects are created. No parent-child graph is built.

---

## Path classification — PathClassifier

`data_management/utils/path_classifier.py`

`classify_path(company_name, path)` returns `path_type`, `canonical_key`, and `primary_category_slug`.

**path_type** is determined by the root node against frozensets:
- `canonical_taxonomy` — real grocery browse hierarchy (default)
- `seasonal` — christmas, easter, limited time only, special buys, etc.
- `promotion` — down down, bonus credit products, everyday market, big night in, specials, etc.
- `dietary` — dietary & world foods, vegan & vegetarian, gluten free, halal, etc.
- `brand_collection` — nescafe, heinz, barilla, cadbury, etc.
- `merchandising` — lunch box, dinner, easy meals, meal kits, back to school, etc.
- `unknown` — unrecognized root (worth logging; indicates new category structure from a supermarket)

**canonical_key** — slugified path joined by `/`. If `category_node_equivalences.json` exists (produced by the agent classification workflow below), node names are normalized to their cross-company canonical form before slugifying. Without that file, the key is company-specific.

**primary_category_slug** — derived by scanning the path from leaf to root through `CATEGORY_MAPPINGS` in `category_mappings.py`. Returns the first non-None match, slugified. Promotional and seasonal paths will typically return `''` because their root names don't appear in `CATEGORY_MAPPINGS`.

---

## Primary category assignment — PrimaryCategoriesGenerator

`data_management/utils/generation_utils/primary_categories_generator.py`

Run via `python manage.py generate --primary-cats`. Steps:

1. Deletes and recreates all `PrimaryCategory` objects from the unique values in `CATEGORY_MAPPINGS`.
2. Sets up `PRIMARY_CATEGORY_HIERARCHY` sub-category links (e.g. Dairy → [Cheese, Milk, Yogurt]).
3. For each product with `category_paths`, collects `primary_category_slug` values — preferring `canonical_taxonomy` paths, falling back to `dietary`, then any path type.
4. Writes the resulting list to `Product.primary_category_slugs` via `bulk_update`.

`PRIMARY_CATEGORY_HIERARCHY` (defined in `category_mappings.py`) also drives the `ProductListView`: browsing "Dairy" automatically includes products tagged Cheese, Milk, and Yogurt.

---

## Cross-company canonical keys — agent classification workflow

By default, `canonical_key` is company-specific: "Hair Care" (Coles) and "Hair Treatments" (Woolworths) produce different keys even if they mean the same thing. The agent workflow resolves this.

**How suspects are generated**

When a product has paths from multiple companies, the path nodes are aligned from the leaf upward and paired company-vs-company at each depth. For example:

```
Woolworths:  [Dairy, Eggs & Fridge  →  Yoghurt  →  Greek Yoghurt]
Coles:       [Dairy & Fridge        →  Yoghurt  →  Greek Style Yoghurt]

depth 0 (leaf):  "Greek Yoghurt"      ↔  "Greek Style Yoghurt"
depth 1:         "Yoghurt"            ↔  "Yoghurt"
depth 2 (root):  "Dairy, Eggs & Fridge" ↔  "Dairy & Fridge"
```

Each unique cross-company node pair becomes one entry in `data_management/data/category_suspects.jsonl`, with `evidence_count` (how many products produced this pairing), `name_similarity` (0–1 string ratio), and `depth_from_leaf`.

**Running the workflow**

```bash
# Step 1 — generate suspects from the DB
python manage.py generate_category_suspects
# → writes category_suspects.jsonl (undecided entries only, sorted by evidence desc)
# → skips anything already in category_decisions.jsonl

# Step 2 — agent classifies suspects
# Give the agent: category_suspects_agent_prompt.md + category_suspects.jsonl
# The agent calls for each entry:
python manage.py classify_suspect <id> match|not_match|unsure [--note "..."]
# → removes the entry from category_suspects.jsonl
# → appends it to category_decisions.jsonl (permanent archive)
# The agent never sees the same entry twice.

# Step 3 — apply confirmed matches
python manage.py apply_category_decisions
# → reads all "match" entries from category_decisions.jsonl
# → writes category_node_equivalences.json
# → PathClassifier picks this up automatically on next restart
```

**What the agent decides**

- `match` — the two node names refer to the same category concept. They'll share a canonical slug.
- `not_match` — genuinely different categories. No link created.
- `unsure` — ambiguous; add a note. Can be revisited later.

High evidence + high name similarity → confident match. Promotional/seasonal nodes vs real taxonomy → not_match. Very low evidence + dissimilar names → unsure.

**After classification**, `canonical_key` values for newly ingested products will be cross-company comparable for confirmed pairs. Re-run `generate --primary-cats` to propagate any changes downstream.

---

## Pillar pages

`PillarsGenerator` runs via `python manage.py generate --pillars`. Reads `data_management/data/pillar_pages.jsonl` and creates `PillarPage` objects linked to the specified `PrimaryCategory` slugs. Used for the homepage browse section and SEO landing pages.

---

## Data flow

```
Scraper
  └─ product carries category_path per company
       │
       ▼
PathManager  (update --products)
  ├─ classify_path() → path_type, canonical_key, primary_category_slug
  └─ merges into Product.category_paths, increments evidence_count
       │
       ▼
generate --primary-cats
  ├─ recreates PrimaryCategory objects from CATEGORY_MAPPINGS
  ├─ sets up PRIMARY_CATEGORY_HIERARCHY sub-category links
  └─ writes Product.primary_category_slugs from category_paths evidence
       │
       ▼
generate --pillars
  └─ groups PrimaryCategory objects into PillarPage objects
       │
       ▼
Frontend
  ├─ Category filter bar → PrimaryCategory list
  ├─ Product list → filters via primary_category_slugs JSON contains
  ├─ Pillar pages → SEO landing pages
  └─ Substitutions → Lvl3 grouped by primary_category_slug
                      Lvl4 grouped by PRIMARY_CATEGORY_HIERARCHY super-groups

[periodic]
generate_category_suspects → agent classifies → apply_category_decisions
  └─ improves canonical_key cross-company consistency
```

---

## Notes

- **MySQL JSON filtering**: `primary_category_slugs__contains=[slug]` runs a `JSON_CONTAINS` per slug, ORed together. Fast enough now; if it becomes a bottleneck at scale, a junction table is the escape hatch — the migration is just materializing the existing denormalized list.
- **CATEGORY_MAPPINGS maintenance**: new supermarket categories added during scraping silently get no `primary_category_slug` until the mapping file is updated. An `unknown` path_type in logs is the signal.
- **Promotional/seasonal path filtering**: scrapers for Coles, Aldi, and IGA already skip promotional root subtrees during category tree traversal. Coles `DataCleanerColes._pick_canonical_heir` scans all `onlineHeirs` and picks the first non-promotional root before the path reaches PathManager.
