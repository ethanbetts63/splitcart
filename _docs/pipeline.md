# SplitCart Data Pipeline

This document describes the full lifecycle of product data in SplitCart — from scraping to a live, queryable database — including every management command and the environment it runs in.

---

## System Topology

SplitCart has a hard split between two environments:

```
LOCAL MACHINE                           SERVER
─────────────────────────────────────────────────────
Scraping (browsers, store APIs)         Django DB + management commands
Product/category/sub generation         Product ingestion pipeline
                                        All derived-data generation

      JSONL files  ──────upload──────►  inboxes/
      Translation  ◄─────API fetch───  /api/files/brand_translations/
      tables                           /api/files/product_translations/
```

**All scraping happens locally.** The local machine generates raw data files (JSONL) and uploads them to the server's inbox directories. Before each scraping run, the local machine fetches the latest translation tables from the server via an authenticated API endpoint with ETag caching — it only downloads a new copy if the file has changed since the last fetch. It does this becuase scraping is resource intense (expensive on the server/free locally) and because the coles scraper requires a human to solve the captchas. 

**All database writes happen on the server.** Management commands that read inboxes and write to the DB are always server-side.

---

## Full Setup Flow

The sequence below is the complete ordered pipeline to initialise or re-initialise the system from scratch. Some commands have a --dev arg. This is for development. It means that rather than uploading or fetching from the live server, data will be fetched or uploaded to the local environment. In production all the commands are the same just minus the --dev args. 

---

### Step 1 — Restore from Archive
```
python manage.py update --archive          # Server
```
Flushes the database and loads data from the most recent archive snapshot. This is the starting point for a clean re-initialisation.

---

### Step 2 — Build Store Groups
```
python manage.py generate --store-groups   # Server
```
Groups stores into clusters for comparative pricing. Store groups are used throughout the system to compare prices across equivalent locations of the same chain.

---

### Step 3 — First Product Upload
```
python manage.py upload --product --dev    # Local
python manage.py update --products         # Server
```
The local machine uploads scraped product JSONL files to the server's `product_inbox/`. The server then runs the full product ingestion pipeline:

1. **FileReader** — parses and deduplicates each file by `normalized_name_brand_size`
2. **Validation** — checks the file isn't stale (date check) and isn't a partial scrape (90% count check)
3. **ProductManager** — resolves products via three-tier matching: barcode → SKU → normalized string; creates or updates products and SKU links
4. **BrandManager** — links products to brands; discovers and records brand name variations
5. **PriceManager** — creates, updates, or deletes prices for the store; records `was_price` for changed prices
6. **CategoryManager** — creates category objects, parent-child links, and product-to-leaf-category links
7. **Post-processing** — generates translation tables, reconciles duplicate products and brands, prunes category cycles, runs group maintenance, regenerates translation tables, removes orphan products

The product translation table is also written to `scraping/data/` so future scraping runs immediately resolve known product name variations to canonical keys at scrape time, before data even reaches the server.

---

### Step 4 — Load GS1 Prefix Data
```
python manage.py update --gs1              # Server
```
Loads GS1 barcode prefix data, which maps barcode number ranges to the registered company name. For brandless products, this creates a direct link to the canonical brand. For products with a mismatched brand, it adds the incorrect brand as a variation on the canonical brand record (feeding the translation table) without force-changing the product's existing brand FK.

---

### Step 5 — Category Links
```
python manage.py generate --cat-links --dev   # Local
python manage.py upload --cat-links --dev     # Local
python manage.py update --cat-links           # Server
```
The local machine generates category-link data from scraping (the store website's category-to-product tree) and uploads it to the server's inbox. The server then applies the category links to the database.

---

### Step 6 — Second Product Upload
```
python manage.py upload --product --dev    # Local
python manage.py update --products         # Server
```
A second product ingestion pass, run after GS1 prefix data and category links are in place. This pass picks up brand assignments that rely on the prefix data and ensures category links are reflected in the product records.

---

### Step 7 — Substitutions
```
python manage.py generate --subs --dev     # Local
python manage.py upload --subs --dev       # Local
python manage.py update --subs             # Server
```
The local machine generates product substitution recommendations (e.g., "if product A is unavailable, suggest product B"). These require products and prices to already exist. The server applies the substitutions to the database.

---

### Step 8 — Derived Data and Stats

All of the following are server-side generates that run after the core product/price data is stable.

```
python manage.py generate --primary-cats   # Server
```
Assigns primary categories to raw scraped categories using `CATEGORY_MAPPINGS` (see `_docs/categories.md`). Traversal stops at explicitly-mapped boundaries to prevent cross-hierarchy contamination.

```
python manage.py generate --bargain-stats  # Server
```
Generates company-level price comparison statistics used to surface bargain products and competitive insights on the frontend.

```
python manage.py generate --pillars        # Server
```
Creates `PillarPage` objects from `data_management/data/pillar_pages.jsonl`, grouping primary categories into homepage landing pages.

```
python manage.py generate --price-comps    # Server
```
Generates cross-store price comparison data for the `PriceComparisonChart` components on pillar and category pages.

```
python manage.py update --faqs             # Server
```
Updates FAQ content associated with category and pillar pages.

```
python manage.py generate --store-stats    # Server
```
Generates store-level statistics (data freshness, product counts, etc.) for monitoring and display.

```
python manage.py generate --price-summaries  # Server
```
Generates aggregated price summary text used on pillar and category pages (e.g. "X% of Fruit products were cheaper at Woolworths than Coles").

```
python manage.py generate --default-stores   # Server
```
Sets the default anchor store list — the stores used as the reference point when a user hasn't selected their own. This is mainly so that initial load for new visitors to the site already has data cached on the server. Hence faster load speed. 

```
python manage.py import_postcodes            # Server
```
Imports Australian postcode-to-suburb data into the `Postcode` model, used for store-proximity features.

---

## Data Flow Summary

```
Local scraper
  └─ Raw store API data
       │
       ▼
BaseDataCleaner (store-specific subclass)
  └─ ProductNormalizer
       ├─ Fetches brand_translation_table from server (ETag-cached)
       ├─ Fetches product_translation_table from server (ETag-cached)
       ├─ Normalizes brand (bag-of-words → translation lookup)
       ├─ Extracts and standardizes sizes
       └─ Generates normalized_name_brand_size (bag-of-words → translation lookup)
       │
       ▼
JSONL file (one line per product, with metadata)
  └─ uploaded via: upload --product
       │
       ▼ (server)
UpdateOrchestrator (update --products)
  ├─ ProductManager     → creates/updates Product + SKU objects
  ├─ BrandManager       → links products to brands, records variations
  ├─ PriceManager       → creates/updates/deletes Price objects
  ├─ CategoryManager    → creates Category objects + hierarchy + product links
  └─ Post-processing
       ├─ TranslationTableGenerators  → writes brand + product .py tables
       ├─ BrandReconciler             → merges duplicate brands
       ├─ ProductReconciler           → merges duplicate products
       ├─ CategoryCycleManager        → prunes circular category links
       ├─ GroupMaintenanceOrchestrator→ maintains store group integrity
       ├─ TranslationTableGenerators  → regenerates tables post-reconciliation
       └─ OrphanProductCleaner        → removes products with no prices
       │
       ▼
generate --primary-cats     → assigns primary categories to raw categories
generate --pillars          → groups primary categories into pillar pages
generate --bargain-stats
generate --price-comps
generate --price-summaries
generate --store-stats
generate --default-stores
       │
       ▼
Frontend
  ├─ Product list → filters by primary_category__slug, store, price
  ├─ Pillar pages → SEO landing pages grouping primary categories
  ├─ Price charts → powered by price-comp and price-summary data
  └─ Cart splitter → uses substitutions + prices to find cheapest combination
```

---

## Known Issues / Design Notes

- **Translation table sync**: The server holds the canonical translation tables. The local scraping environment fetches a copy before each run via an ETag-cached API request. The two copies can appear to differ in size if scraping hasn't run recently — the local copy is simply an older snapshot.
- **Two product passes**: Products are ingested twice in a full setup (steps 3 and 6) because the GS1 prefix data loaded in step 4 improves brand matching, and the second pass propagates those improvements.
- **Category assignment is manual**: `generate --primary-cats` is not part of `update --products`. It must be run separately whenever the category mapping file is updated or after a large new batch of products is ingested.
