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

## Design Notes

- **Two product passes**: Products are ingested twice in a full setup (steps 3 and 6) because the GS1 prefix data loaded in step 4 improves brand matching, and the second pass propagates those improvements. the second pass isnt strictly necessary but it doubles the speed at which the system learns. 
- **Category assignment is manual**: `generate --primary-cats` is not part of `update --products`. It must be run separately whenever the category mapping file is updated or after a large new batch of products is ingested.
