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

**All scraping happens locally.** The local machine generates raw data files (JSONL) and uploads them to the server's inbox directories. Before each scraping run, the local machine fetches the latest translation tables from the server via an authenticated API endpoint. It works this way because scraping is resource intense (expensive on the server, free locally) and because the Coles scraper needs a human to solve the captchas.

The tables are re-downloaded in full every run. The server sets an `ETag`, but `fetch_python_file` never sends `If-None-Match` and never persists one — `test_ignores_etag_when_present` and `test_does_not_send_etag_header_if_cached` in `scraping/tests/util_tests/test_python_file_downloader.py` pin that deliberately. Any document claiming the fetch is ETag-cached is describing an intention, not the code.

**All database writes happen on the server.** Management commands that read inboxes and write to the DB are always server-side.

**Some generation steps are local-only.** Substitution generation (`generate --subs`) cannot run on the server. It depends on heavy ML libraries (SentenceTransformer etc.) that are only in `requirements_dev.txt` — the server runs the leaner `requirements.txt` to keep costs down. This step runs locally, produces JSONL output, and uploads it like any other file. The local machine must download the full product list from the server to do meaningful work, which can be a significant payload. The download is well-optimized but worth knowing about when the pipeline feels slow at that step.

---

## Full Setup Flow

`reset_db` is the rebuild entrypoint. It resets the schema using existing migrations, replays archived company and product data, then regenerates derived database state.

```
python manage.py reset_db                  # LOCAL  - reset DB, replay archive, regenerate derived state
python manage.py reset_db --server         # SERVER - git pull, migrate, replay archive, regenerate derived state
```

The normal local/server update flow remains:

```
python manage.py upload --products --dev   # LOCAL  - uploads product JSONL and archives a tracked copy
python manage.py update --products         # SERVER - ingests products, brands, prices, category paths

python manage.py generate --cat-links --dev # LOCAL - generates category links
python manage.py upload --cat-links --dev   # LOCAL - uploads category links
python manage.py update --cat-links         # SERVER - ingests category links

python manage.py generate --subs --dev     # LOCAL  - generates substitutions
python manage.py upload --subs --dev       # LOCAL  - uploads substitutions
python manage.py update --subs             # SERVER - ingests substitutions

python manage.py generate --primary-cats   # SERVER - assigns primary categories from category_paths
python manage.py generate --pillars        # SERVER - creates pillar pages
python manage.py generate --bargain-stats  # SERVER - computes bargain comparison stats
python manage.py generate --price-comps    # SERVER - computes category price comparisons
python manage.py generate --price-summaries # SERVER - computes product price summaries
python manage.py generate --default-companies # SERVER - stores default pricing companies
```

## Product Archive

Base company data is stored as a tracked archive seed:

```text
pipeline/data/archive/company_archive/companies.json
```

`update --companies --archive` upserts those company rows and must run before archived product replay.

Product JSONL files are archived after upload:

```text
pipeline/data/archive/product_archive/
```

`update --products --archive` reads product JSONL files from `pipeline/data/archive/product_archive/` and preserves those files after ingest. Normal `update --products` still reads from `pipeline/data/inboxes/product_inbox/`.

## Data Flow Summary

```
Local scraper
  └─ Raw supermarket API data
       │
       ▼
scrape._fetch_translation_tables()
  ├─ downloads brand_translation_table.json
  └─ downloads product_normalized_name_brand_size_translation_table.json
       │
       ▼
BaseDataCleaner (per-company subclass, loads both tables from disk)
  └─ ProductNormalizer
       ├─ Normalizes brand (bag-of-words → translation lookup)
       ├─ Extracts and standardizes sizes
       └─ Generates normalized_name_brand_size (bag-of-words → translation lookup)
       │
       ▼
JSONL file (one line per product, with metadata)
  └─ uploaded via: upload --products
       │
       ▼ (server)
UpdateOrchestrator (update --products)
  ├─ ProductManager     → creates/updates Product + SKU objects
  ├─ BrandManager       → links products to brands, records variations
  ├─ PriceManager       → creates/updates/deletes Price objects
  ├─ PathManager        → merges category_path evidence into Product.category_paths
  └─ Post-processing
       ├─ TranslationTableGenerators  → writes brand + product .json tables
       ├─ BrandReconciler             → merges duplicate brands
       ├─ ProductReconciler           → merges duplicate products
       ├─ TranslationTableGenerators  → regenerates tables post-reconciliation
       └─ OrphanProductCleaner        → removes products with no prices
       │
       ▼
generate --primary-cats     → derives primary_category_slugs from Product.category_paths
generate --pillars          → groups primary categories into pillar pages
generate --bargain-stats
generate --price-comps
generate --price-summaries
generate --default-companies
       │
       ▼
Frontend
  ├─ Product list → filters by primary_category_slugs (JSON contains), company, price
  ├─ Pillar pages → SEO landing pages grouping primary categories
  ├─ Price charts → powered by price-comp and price-summary data
  └─ Cart splitter → uses substitutions + prices to find cheapest combination
```

---

## Frontend User Journey

The frontend is a Next.js App Router application that consumes the generated data through three primary phases:

### Phase 1: Discovery & Configuration

Users navigate the catalog via the **Homepage** categories, **Search**, or **Pillar Pages** (SEO-optimized landing pages grouping primary categories). There is nothing to configure: the pricing company set is global, read from `get_default_company_ids()`, because Coles, Woolworths and Aldi all price nationally.

### Phase 2: Cart & Substitutions

Products are added to a persistent cart. Before optimization, users go through a **Substitution Approval** flow where they can accept alternative products (e.g., different brands or sizes). This step is critical as it provides the optimizer with more data points to find deeper savings.

### Phase 3: Optimization & Final Plan

The **Optimizer** calculates the cheapest combination of companies for the approved list. The results are presented as multiple plans (e.g. best single company vs. a three-company split), showing total savings and a company-by-company breakdown. Users can then export their optimized shopping list as a PDF or via email.

---

## Design Notes

- **Category paths are incremental**: `PathManager` merges path evidence into `Product.category_paths` on every ingest — it increments `evidence_count` for paths already seen and appends new ones. The `canonical_key` for each path improves over time as cross-company node equivalences are confirmed via the agent classification workflow (see `_docs/categories.md`).
- **Primary category assignment is manual**: `generate --primary-cats` must be run separately after ingesting a large new batch of products or after updating `CATEGORY_MAPPINGS`. It reads `Product.category_paths` and writes `Product.primary_category_slugs` — no graph traversal, no raw Category objects.
- **Substitution generation no longer needs category data**: `generate --subs` fetches only the product list from the server. Lvl3 groups by `primary_category_slugs`; Lvl4 uses `PRIMARY_CATEGORY_HIERARCHY` parent-child groups. No category or category-link API endpoints are fetched.
