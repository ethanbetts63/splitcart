# SplitCart Data Pipeline

This document describes the full lifecycle of product data in SplitCart — from scraping to a live, queryable database.

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

**Some generation steps are local-only.** Substitution generation (`generate --subs`) cannot run on the server. It depends on heavy ML libraries (SentenceTransformer etc.) that are only in `requirements_dev.txt` — the server runs the leaner `requirements.txt` to keep costs down. This step runs locally, produces JSONL output, and uploads it like any other file. The local machine must download the full product list from the server to do meaningful work, which can be a significant payload. The download is well-optimized but worth knowing about when the pipeline feels slow at that step.

---

## Full Setup Flow

The sequence below is the complete ordered pipeline to initialise or re-initialise the system from scratch. Commands marked **LOCAL** use heavy ML dependencies and must run on the local machine — they will not work on the server. Commands marked **SERVER** must run on the server where the DB lives. The `--dev` flag redirects uploads/downloads to the local environment instead of the live server; omit it in production.

```
python manage.py update --archive          # SERVER  — archives stale price data
python manage.py generate --store-groups   # SERVER  — initialises one group per store

python manage.py upload --product --dev    # LOCAL   — uploads scraped product JSONL
python manage.py update --products         # SERVER  — ingests products, brands, prices, category paths

python manage.py update --prefixes         # SERVER  — processes GS1 prefix inbox

python manage.py upload --product --dev    # LOCAL   — second product pass (GS1 data now improves brand matching)
python manage.py update --products         # SERVER  — re-ingests with improved brand translations

python manage.py generate --primary-cats   # SERVER  — assigns primary categories from category_paths
python manage.py generate --pillars        # SERVER  — creates pillar pages

python manage.py generate --subs --dev     # LOCAL   — generates substitutions (SentenceTransformer, ML-heavy)
python manage.py upload --subs --dev       # LOCAL   — uploads substitution JSONL
python manage.py update --subs             # SERVER  — ingests substitutions
```

See Design Notes below for why products are ingested twice.

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
  ├─ PathManager        → merges category_path evidence into Product.category_paths
  └─ Post-processing
       ├─ TranslationTableGenerators  → writes brand + product .py tables
       ├─ BrandReconciler             → merges duplicate brands
       ├─ ProductReconciler           → merges duplicate products
       ├─ GroupMaintenanceOrchestrator→ maintains store group integrity
       ├─ TranslationTableGenerators  → regenerates tables post-reconciliation
       └─ OrphanProductCleaner        → removes products with no prices
       │
       ▼
generate --primary-cats     → derives primary_category_slugs from Product.category_paths
generate --pillars          → groups primary categories into pillar pages
generate --bargain-stats
generate --price-comps
generate --price-summaries
generate --store-stats
generate --default-stores
       │
       ▼
Frontend
  ├─ Product list → filters by primary_category_slugs (JSON contains), store, price
  ├─ Pillar pages → SEO landing pages grouping primary categories
  ├─ Price charts → powered by price-comp and price-summary data
  └─ Cart splitter → uses substitutions + prices to find cheapest combination
```

---

## Frontend User Journey

The frontend is a React SPA that consumes the generated data through three primary phases:

### Phase 1: Discovery & Configuration
Users navigate the catalog via the **Homepage** categories, **Search**, or **Pillar Pages** (SEO-optimized landing pages grouping primary categories). During this phase, users select their preferred local stores in the **Settings** dialog to filter pricing and availability.

### Phase 2: Cart & Substitutions
Products are added to a persistent cart. Before optimization, users go through a **Substitution Approval** flow where they can accept alternative products (e.g., different brands or sizes). This step is critical as it provides the optimizer with more data points to find deeper savings.

### Phase 3: Optimization & Final Plan
The **Optimizer** calculates the cheapest combination of stores for the approved list. The results are presented as multiple plans (e.g., Best Single Store vs. Best 3-Store Split), showing total savings and a store-by-store breakdown. Users can then export their optimized shopping list as a PDF or via email.

---

## Design Notes

- **Two product passes**: Products are ingested twice in a full setup because the GS1 prefix data loaded between passes improves brand matching. The second pass propagates those improvements. It isn't strictly necessary but doubles the speed at which the system learns.
- **Category paths are incremental**: `PathManager` merges path evidence into `Product.category_paths` on every ingest — it increments `evidence_count` for paths already seen and appends new ones. The `canonical_key` for each path improves over time as cross-company node equivalences are confirmed via the agent classification workflow (see `_docs/categories.md`).
- **Primary category assignment is manual**: `generate --primary-cats` must be run separately after ingesting a large new batch of products or after updating `CATEGORY_MAPPINGS`. It reads `Product.category_paths` and writes `Product.primary_category_slugs` — no graph traversal, no raw Category objects.
- **Substitution generation no longer needs category data**: `generate --subs` fetches only the product list from the server. Lvl3 groups by `primary_category_slugs`; Lvl4 uses `PRIMARY_CATEGORY_HIERARCHY` parent-child groups. No category or category-link API endpoints are fetched.
