# Scraping App

All scraping runs locally. Output is JSONL files uploaded to the server.

---

## Flow

```
scrape (management command)
  │
  ├─ fetch translation tables from server (ETag-cached)
  │    ├─ brand_translation_table.py
  │    └─ product_normalized_name_brand_size_translation_table.py
  │
  ├─ [--coles]  ColesSessionManager (Selenium warm-up + cookie bridge)
  │               └─ ColesScraperV2 × all Coles stores
  │                    └─ output → barcode_scraper_inbox/
  │                         └─ scrape_barcodes (phase 2)
  │                              └─ prefill known barcodes from DB API
  │                                   └─ scrape individual product pages for GTINs
  │
  └─ [--woolworths/--aldi/--iga]  scheduler worker
       └─ polls /api/scheduler/next-candidate/ in a loop
            └─ BaseProductScraper
                 ├─ get categories (live API call per store)
                 ├─ paginate through each category → raw product list
                 ├─ DataCleaner{Company}
                 │    ├─ field_map  (raw API field → standard schema)
                 │    ├─ _transform_product  (store-specific logic)
                 │    └─ _post_process_product (runs on every product, every chain)
                 │         ├─ ProductNormalizer
                 │         │    ├─ normalized_brand  (bag-of-words → translation lookup)
                 │         │    ├─ sizes  (extracted from name/brand/size, canonicalized)
                 │         │    └─ normalized_name_brand_size  (dedup key)
                 │         ├─ PriceNormalizer  (→ unit_price, unit_of_measure)
                 │         └─ generate_price_hash
                 └─ JsonlWriter
                      ├─ dedup by normalized_name_brand_size (in-memory set)
                      ├─ write to temp file
                      └─ commit (move to product_outbox) or cleanup (delete on failure)
```

---

## Complexities

### Translation tables (ETag caching)

Before each run, `scrape` fetches two Python files from the server — the brand and product translation tables. These map normalized product/brand strings to their canonical equivalents and are generated server-side after each ingestion run. They're fetched with `If-None-Match` so a `304` skips the download entirely. Each `.py` file contains a single dict assignment loaded locally with `ast.literal_eval`.

### normalized_name_brand_size (bag-of-words dedup key)

The central identity key for a product across chains. Built by:
1. Concatenating `name + normalized_brand + sizes`.
2. Lowercasing, stripping punctuation, splitting into words, sorting alphabetically, rejoining.
3. Looking up the result in `product_translations` — if a canonical key exists, use it.

Sorting words means `"Coca Cola 375ml Can"` and `"Can Coca-Cola 375ml"` produce the same key. This handles the fact that different chains write the same product name differently. The translation table handles cases where even the bag-of-words key diverges between chains.

The same key is used for in-scrape deduplication (`JsonlWriter` drops products already written this session) and for cross-store product matching on the server.

### Coles two-phase scraping

Coles category browse pages return product data but not barcodes — those are only on individual product pages. Rather than hit a product page for every product during the browse (slow, more CAPTCHA exposure), phase 1 writes everything to `barcode_scraper_inbox` and phase 2 only fetches product pages for SKUs where the barcode isn't already in the DB.

**ColesSessionManager** — Coles requires a live browser session to pass bot detection. The manager launches Chrome via Selenium, waits for the user to solve any CAPTCHA (detected by `__NEXT_DATA__` appearing in the DOM), then copies browser cookies into a `requests.Session`. All actual fetching uses the `requests.Session`; the browser stays open only to hold session state. When switching stores, it updates the `fulfillmentStoreId` cookie in the live browser, refreshes, re-syncs cookies. `is_blocked()` checks for the absence of `__NEXT_DATA__` in a response.

Phase 2 (`scrape_barcodes`) also uses a `.progress` sidecar file (one JSON line per completed product) so it can resume mid-file after a block or crash.

### Store-specific category fetching

Woolworths and Coles use the same category list for every store. Aldi and IGA fetch a category tree per store from their API and use only leaf nodes (recursive traversal). IGA also has an extra pagination guard: if the current page returns the same SKU set as the previous page, it stops (their API repeats the last page instead of returning empty).

### JsonlWriter commit/cleanup

JSONL files are written to a temp directory. On a successful scrape they're moved to the final outbox (`shutil.move`). On failure the temp file is deleted. This means the outbox never contains partial files from crashed scrapes.


### ProductNormalizer

`scraping/utils/product_scraping_utils/product_normalizer.py`

Called by `_post_process_product()`. Takes the cleaned product dict and both translation tables.

**Brand normalization (`normalized_brand`)**

1. Takes the raw brand string and applies `_clean_value()`: NFKD unicode normalize → ASCII → lowercase → strip all punctuation/symbols → split into words → sort alphabetically → rejoin. This produces a "bag of words" key.
2. Looks up that key in `brand_translations`. If found, returns the canonical normalized brand string. If not, returns the generated key itself.

The result stored as `normalized_brand` is not human-readable — it's the cross-store brand identity key used for matching on the server.

**Size extraction (`sizes`)**

Sizes are extracted from three fields: `name`, `brand`, `size`. The extractor handles:
- Simple: `500g`, `1.5l`, `100ml`
- Ranges: `300-400g` → adds both `300g` and `400g`
- Multipacks: `6 x 375ml` → adds `6pk` and `375ml`; `375ml x 6` → same
- Standalone units (e.g., `"each"` alone in a string)

After extraction, sizes go through two passes:
1. Text standardization: `"pack"` → `"pk"`, `"each"` → `"ea"`, `"1ea"` → `"ea"`.
2. Canonical numerical conversion using `SizeComparer._parse_size()`: converts `"0.5kg"` → `"500g"`, de-duplicates by canonical `(value, unit)` tuple, formats integers without trailing `.0`.

Result is a sorted list stored as `sizes`.

**Normalized name string (`normalized_name_brand_size`)**

This is the primary de-duplication key used throughout the pipeline.

1. Concatenate: `"{name} {normalized_brand} {' '.join(sizes)}"`.
2. Apply `_clean_value()` to the whole string (same bag-of-words treatment as brand).
3. Look up in `product_translations`. If found, return the canonical key. If not, return the generated key.

The bag-of-words approach means `"Coca Cola 375ml Can"` and `"Can Coca-Cola 375ml"` produce the same key, making product identity robust to minor formatting differences between store APIs. 

This a unique field when inputted into the db. Not only does it make data entry more efficient it also creates a self improving system that gets better at matching products over time at stores that dont provide barcodes.

**Barcode cleaning (`barcode`)**

Accepts comma-separated values. Prefers 13-digit EAN-13. Falls back to 12-digit UPC-A (zero-padded to 13). Returns `None` if no valid barcode found. A barcode that equals the SKU is rejected (some APIs return the internal ID in the barcode field).

### PriceNormalizer

`scraping/utils/product_scraping_utils/price_normalizer.py`

Handles per-unit price standardization. Called by `_get_standardized_unit_price_info()` in `BaseDataCleaner`.

**Unit price extraction** — tries `per_unit_price_value` first (direct numeric field). Falls back to parsing `per_unit_price_string` with a `\$?(\d+\.?\d*)` regex (e.g., `"$1.68 per 100 g"` → `1.68`).

**Unit and quantity extraction** — tries `per_unit_price_measure` first, then `per_unit_price_string`. Uses a regex matching an optional number followed by a unit (`100 g`, `kg`, `1EA`, `1.75/l`). Returns a `(standard_unit, quantity)` tuple.

**Standardization** — the base cleaner converts to per 1kg or per 1L:
- `g` with quantity ≠ 1000: `price / quantity * 1000`, measure → `"1kg"`
- `ml` with quantity ≠ 1000: same → `"1l"`
- `kg` with quantity ≠ 1: `price / quantity`, measure → `"1kg"`
- `l` with quantity ≠ 1: `price / quantity`, measure → `"1l"`

Result: `unit_price` (float, 2 dp) and `unit_of_measure` (string).

### Price Hash

`scraping/utils/product_scraping_utils/price_hasher.py`

After all price fields are set, `generate_price_hash()` computes an MD5 hash over: `price_current`, `price_was`, `unit_price`, `unit_of_measure`, `per_unit_price_string`, `is_on_special`. Keys are sorted before JSON serialization to ensure a deterministic hash regardless of dict ordering. Stored as `price_hash` on the product.

On the server, when a price record is being updated, the server compares the incoming `price_hash` against the stored one. If they match, no DB write is needed. This avoids unnecessary writes when prices haven't changed between scrape runs.

### Final Cleanup in `_post_process_product`

- `scraped_date` is set to `timestamp.date().isoformat()`.
- All empty string values are coerced to `None`.
- All `None` values are stripped from the dict (reduces file size).

### Store discovery

Store scrapers (`find_stores`) use a separate base class (`BaseStoreScraper`) and write one JSON file per store to `store_outbox`. Woolworths and Aldi use a coordinate grid covering Australia with a random step size (overlap is deduplicated by an in-memory store ID set). IGA enumerates integer store IDs 1–23,001 via a third-party JSONP endpoint. Coles uses Selenium to make GraphQL calls from inside the browser (cookies are needed; the session isn't copied to `requests`).

### Key ideas

**Commit/cleanup pattern** — JSONL files are written to a temp directory and moved to the outbox only on full success. A crash mid-scrape leaves no partial file in the outbox.

**ETag caching for translation tables** — translation tables can be 10MB+. The ETag check means only changed tables are downloaded. On a typical run where the tables haven't changed, both fetches return `304 Not Modified` in milliseconds.

**Selenium cookie bridging** — for Coles, the human solves the CAPTCHA in a real Chrome browser. The scraper then copies those cookies into a `requests.Session` which does all further API calls. The browser stays open but idle, only re-used when the store ID needs to change or the session expires. This avoids re-solving CAPTCHAs for every store.

**Two-phase Coles scraping** — separates the fast part (category browse, ~1 request per page) from the slow part (individual product pages for barcodes). Phase 1 can be completed entirely before committing to phase 2. Phase 2 skips products where barcodes are already known from the DB.

**Price hash** — a deterministic MD5 over the price fields lets the server skip DB writes for prices that haven't changed since the last scrape, making re-scraping cheap when prices are stable.



