# GS1 Prefix System

GS1 is the international standards body that assigns barcode prefixes. The first 7–12 digits of an EAN-13 barcode are a GS1 license key — a globally unique identifier tied to a specific company. Knowing the prefix means knowing the official manufacturer, regardless of what brand name a store scraped.

This matters because brand names are inconsistent across stores. Woolworths might call a brand "Sanitarium Health Food Company", Coles might call it "Sanitarium". The prefix is ground truth. The GS1 system uses it to normalize brand names, build brand synonym mappings, and link orphaned products to their correct brand.

---

## Key fields on `ProductBrand`

| Field | Source | Meaning |
|---|---|---|
| `confirmed_official_prefix` | GS1 website (scraped) | The GS1 license key for this brand — authoritative |
| `longest_inferred_prefix` | Barcode LCP analysis | Best-guess prefix derived from common barcode digits when no confirmed prefix exists |
| `name_variations` | GS1 reconciliation / inference | Raw brand name strings confirmed to be synonyms |
| `normalized_name_variations` | Same | Normalized versions — feeds the brand translation table |

---

## Two ways to learn a prefix

### 1. Confirmed — GS1 website scrape (authoritative)

**Files:** `scraping/scrapers/gs1_company_scraper.py`, `data_management/views/gs1_views.py`

The scraper runs locally. It targets brands that have no `confirmed_official_prefix` yet, prioritized by product count (most products first, top 30 per run).

**Session initialization:** GS1's Verified-by-GS1 service requires cookies set by a browser. On first run, Selenium opens Chrome, pauses for the human to accept the cookie banner, then harvests the session cookies and `form_build_id`. All subsequent requests within the run use a `requests.Session` with those cookies — no browser needed per lookup. Max 30 successful scrapes before stopping; aborts after 5 consecutive failures. 30 is the number of searches a day GS1 allows. 

For each brand: fetch a sample barcode from the server (`GET /api/brands/{id}/sample-barcode/`), POST it to the GS1 AJAX endpoint, parse the license key and company name from the HTML response. Results are written to `gs1_outbox/` as JSONL.

### 2. Inferred — Longest Common Prefix analysis

**File:** `data_management/management/commands/infer_and_reconcile_brands.py`

> **Not currently wired into the pipeline.** This command exists and runs standalone but is not called by any orchestrator or scheduled step. I have yet to properly test my idea. I think their system works like a subnet mask in the sense that companies buy a certain range of "barcodes" (addresses) so that they can have unique identifiers for all their products. But if wrong I'll pollute the db so I've left this for now. If im right on the other hand it could actually be a really powerful way to normalize brand names. Even though its only 30 brands a day, we start with the brands with the most products, and it all adds up.

For brands that haven't been scraped yet. Collects all barcodes for a brand and finds their longest common prefix (LCP). Validates the prefix length against the GS1 address space rule: a prefix of length N can address `10^(12−N)` unique items — the inferred prefix can't be so long that there isn't room for the number of products we already have. The longest prefix that passes this check is stored as `longest_inferred_prefix`.

Phase 2 then uses the inferred prefix to find products with that prefix linked to a *different* brand and records those brand names as variations on the canonical brand.

---

## Ingestion flow (confirmed prefix path)

```
Local machine
  Fetch top 30 unconfirmed brands  ← GET /api/gs1/unconfirmed-brands/
  For each brand:
    Fetch sample barcode            ← GET /api/brands/{id}/sample-barcode/
    Query GS1 Verified-by-GS1
    Extract license_key + company_name
  Write to gs1_outbox/*.jsonl
  Compress + upload                 → POST /api/upload/gs1/
        │
        ▼ (server)
  update --gs1  →  GS1UpdateOrchestrator
    For each JSONL record:
      get_or_create canonical brand (GS1 company name)
      set confirmed_official_prefix on canonical brand
      find products with barcode starting with prefix:
        - wrong brand attached  → record that brand name as a variation
        - no brand attached     → link directly to canonical brand
  JSONL deleted from inbox after processing
        │
        ▼
  TranslationTableGenerators regenerate brand_translation_table.py
  Next scrape fetches updated table → brands normalized correctly at scrape time
```

---

## Brand translation table

**File:** `data_management/.../translation_table_generators/brand_translation_table_generator.py`

Reads all `ProductBrand.normalized_name_variations` and writes a `variation → canonical` mapping to `brand_translation_table.py`. This is the file `ProductNormalizer` uses at scrape time to resolve raw brand strings to their canonical normalized key before generating `normalized_name_brand_size`.

**Circular dependency handling:** If brand A lists B as a variation and brand B also lists A as a variation, a conflict exists. Resolved by a four-tier tiebreaker:
1. Has `confirmed_official_prefix` (GS1 data wins)
2. Higher product count
3. More recorded variations
4. Alphabetical

---

## Diagnostic tool

`python manage.py prefix_report` — scans all products with barcodes against all confirmed prefixes and writes a human-readable discrepancy report to `brand_discrepancy_report.txt`. Used to audit the state of brand assignment without modifying any data.

---

## Key files

| File | Role |
|---|---|
| `scraping/scrapers/gs1_company_scraper.py` | Scrapes GS1 Verified-by-GS1 for license keys |
| `data_management/views/gs1_views.py` | `unconfirmed-brands` + `sample-barcode` API endpoints |
| `scraping/utils/command_utils/gs1_uploader.py` | Compresses and uploads outbox JSONL to server |
| `data_management/views/gs1_file_upload_view.py` | Receives and decompresses uploaded GS1 files |
| `data_management/database_updating_classes/gs1_update_orchestrator.py` | Processes inbox — sets prefixes, records variations, links orphans |
| `data_management/management/commands/infer_and_reconcile_brands.py` | LCP-based prefix inference for unscraped brands |
| `data_management/.../brand_translation_table_generator.py` | Builds `variation → canonical` brand map from recorded variations |
| `data_management/management/commands/prefix_report.py` | Diagnostic: writes brand discrepancy report to file |
