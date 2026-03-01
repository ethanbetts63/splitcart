  ---
  Scraping App — Investigation Report

  Bugs

  1. Aldi unit price double-division (DataCleanerAldi.py:34, price_normalizer.py:77)
  DataCleanerAldi._transform_product() divides per_unit_price_value by 100 (cents → dollars). Then _get_standardized_unit_price_info() passes that
  value to PriceNormalizer, which divides by 100 again when company == 'aldi'. The result is an Aldi unit price 10,000x too small.

  ~~2. product_uploader.py is defined twice — DONE~~

  3. BaseStoreScraper infinite recursion (base_store_scraper.py:60-64)
  except Exception as e:
      ...
      time.sleep(10)
      self.run()  # recursive with no limit
  Any persistent error (API change, auth failure) causes infinite recursion and eventual stack overflow. There's no retry counter or bail-out.

  4. GS1 scraper ignores base_url (gs1_company_scraper.py:30)
  base_url = "http://127.0.0.1:8000" is hardcoded. The parent scrape command computes base_url from --dev and passes nothing to Gs1CompanyScraper.
  So --gs1 always talks to localhost even in production context. It would just fail silently on a machine without a local server.

  ---
  Dead Code

  ~~5. save_to_inbox.py — DONE (deleted)~~

  6. get_store_specific_categories_coles.py — A GraphQL-based dynamic category fetcher. Has no .pyc, is never imported. The dynamic approach was
  written but never wired in. Meanwhile get_coles_categories.py has a TODO: Implement a more robust way comment. These two files exist in a stalled
  state — the solution exists but was never connected.

  ~~7. atomic_scraping_utils.py — DONE (finalize_scrape inlined into jsonl_writer.py, file deleted)~~

  ~~8. JsonlWriter.finalize() method — DONE (deleted)~~

  ~~9. ProductScraperAldi.post_scrape_enrichment — DONE~~

  ~~10. --woolworths2 flag in find_stores.py — DONE~~

  ~~11. Orphaned shop_scraping_utils/migrations/ — DONE~~

  12. Stale .pyc files for deleted sources: __pycache__ contains barcode_scraper_coles.cpython-312.pyc and product_scraper_coles.cpython-312.pyc —
  both V1 scrapers deleted and replaced by V2 — but the compiled bytecode remains.

  ---
  Architectural / Logic Issues

  13. Brand cache + translation tables rebuilt per category (BaseDataCleaner.py:27-28)
  BaseDataCleaner.__init__() calls _build_brand_cache() (full DB query: ProductBrand.objects.all()) and _load_translation_tables() (reads +
  ast.literal_evals two large Python files) on every instantiation. Since a new cleaner is created per category (clean_raw_data() instantiates a new
   DataCleanerXxx every call), a Woolworths scrape of 80 categories hits the DB 80 times and parses the translation files 80 times, all for the same
   data.

  14. Coles worker never fetches translation tables (scrape.py:29-31)
  The --coles path returns immediately at line 31 before the translation table download that happens at lines 34-39 for the legacy path. If you only
   ever run --coles, your local translation tables are whatever was last downloaded by a different run.

  15. ColesBarcodeScraperV2 calls super().__init__() from setup() (barcode_scraper_coles_v2.py:54)
  The class manually initializes attributes in __init__() and then calls super().__init__() from inside setup(). This is a significant departure
  from the expected inheritance contract — self.output is set to None in __init__() (line 23) rather than a valid ScraperOutput, meaning any error
  logging before setup() completes would crash.

  16. DataCleanerWoolworths defines deep_get / parse_json_field inside _transform_product (DataCleanerWoolworths.py:31-46)
  These inner functions are recreated on every single product (not every category, every product). They should be module-level helpers or class
  methods.

  17. BaseDataCleaner.clean_data() unnecessary two-pass structure (BaseDataCleaner.py:111-133)
  It loops through all products to build self.cleaned_products, then loops again to build self.final_products. Each product is processed entirely
  independently — there's no reason for two passes. It doubles the iteration and wastes memory.

  ~~18. StoreUploader uses __file__-relative paths — DONE~~

  19. scrape --gs1 fetches translation tables unnecessarily (scrape.py:34-39)
  The --gs1 branch is checked at lines 51-55, after translation tables are downloaded at lines 34-39. GS1 scraping has nothing to do with product
  translation tables.

  ---
  Inconsistencies

  20. IGA company name lowercase mismatch (scrape_barcodes.py:25 vs rest of pipeline)
  ColesBarcodeScraperV2 hardcodes self.company = "coles" (lowercase). Every other path gets the company name from store.company.name in the DB (e.g.
   "Coles" with capital). PriceNormalizer does self.company.lower() == 'aldi', so the case doesn't matter there. But metadata written to JSONL files
   from the barcode scraper would have "coles" lowercase while regular scrapes write "Coles". The ingestion pipeline may be case-insensitive enough
  that this doesn't break anything, but it's inconsistent.

  21. Aldi/IGA dev attribute stored but unused (product_scraper_aldi.py:19, product_scraper_iga.py:21)
  Both scrapers store self.dev = dev. Aldi passes it to get_aldi_categories() but that function also stores it without using it. IGA doesn't pass it
   anywhere. The dev parameter propagated through the Aldi/IGA path is completely inert.

  ~~22. base_product_scraper.py uses print() — DONE~~

  23. no change needed. 

  24. PascalCase module filenames (DataCleanerAldi.py, BaseDataCleaner.py, etc.)
  Python convention is snake_case for module filenames. All other utils in the codebase use lowercase. This is a cosmetic inconsistency but causes
  slightly awkward imports.

  ~~25. ScraperOutput.update_progress() — manual max logic — DONE~~

  ---
  Summary Table

  ┌───────┬──────────────────────────────────────────┬──────────┬───────────────┐
  │   #   │                   File                   │ Severity │     Type      │
  ├───────┼──────────────────────────────────────────┼──────────┼───────────────┤
  │ 1     │ DataCleanerAldi.py + price_normalizer.py │ High     │ Bug           │
  ├───────┼──────────────────────────────────────────┼──────────┼───────────────┤
  │ 2     │ product_uploader.py                      │ High     │ Bug           │
  ├───────┼──────────────────────────────────────────┼──────────┼───────────────┤
  │ 3     │ base_store_scraper.py                    │ High     │ Bug           │
  ├───────┼──────────────────────────────────────────┼──────────┼───────────────┤
  │ 4     │ gs1_company_scraper.py                   │ Medium   │ Bug           │
  ├───────┼──────────────────────────────────────────┼──────────┼───────────────┤
  │ 5-12  │ Various                                  │ Low      │ Dead code     │
  ├───────┼──────────────────────────────────────────┼──────────┼───────────────┤
  │ 13    │ BaseDataCleaner.py                       │ High     │ Performance   │
  ├───────┼──────────────────────────────────────────┼──────────┼───────────────┤
  │ 14    │ scrape.py                                │ Medium   │ Logic         │
  ├───────┼──────────────────────────────────────────┼──────────┼───────────────┤
  │ 15    │ barcode_scraper_coles_v2.py              │ Medium   │ Architecture  │
  ├───────┼──────────────────────────────────────────┼──────────┼───────────────┤
  │ 16    │ DataCleanerWoolworths.py                 │ Low      │ Performance   │
  ├───────┼──────────────────────────────────────────┼──────────┼───────────────┤
  │ 17    │ BaseDataCleaner.py                       │ Low      │ Architecture  │
  ├───────┼──────────────────────────────────────────┼──────────┼───────────────┤
  │ 18    │ store_uploader.py etc.                   │ Low      │ Inconsistency │
  ├───────┼──────────────────────────────────────────┼──────────┼───────────────┤
  │ 19    │ scrape.py                                │ Low      │ Logic         │
  ├───────┼──────────────────────────────────────────┼──────────┼───────────────┤
  │ 20-25 │ Various                                  │ Low      │ Inconsistency │
  └───────┴──────────────────────────────────────────┴──────────┴───────────────┘


  Normalizer — Real Gaps (from looking at actual data)

  1. IGA sellBy contaminates every size field (DataCleanerIga.py:59–62)

  From the raw data, sellBy is "Each" on both products. The cleaner does:
  size_str = f"{size_value}{size_type}"  # "1l", "200ml"
  if sell_by:
      size_str += f" {sell_by}"          # "1l Each", "200ml Each"

  Then _extract_all_sizes() runs on "1l Each" → extracts both "1l" and "ea". So every IGA product gets "ea" added to its sizes list even though it
  means nothing different from any other product. The "Each" in sellBy means the unit of sale, not a multipack size — it shouldn't be in the size
  string at all. You could filter sellBy = "Each" from the appended string.

  2. Aldi fractional kg sizes don't match other stores

  From the raw Aldi data: "sellingSize": "0.11 kg" (Goat Cheese), "0.8 kg" (Marinara). The size extractor produces "0.11kg" and "0.8kg". But the
  same products at Woolworths or Coles would list as "110g" and "800g". If SizeComparer._parse_size doesn't do cross-unit conversion (g ↔ kg), these
   won't match for deduplication/substitution purposes. The fix would be to standardize fractional kg values to grams in _get_standardized_sizes() —
   0.11kg → 110g, 0.8kg → 800g.

  3. Unit price boundary edge case (BaseDataCleaner.py:202–213)

  The standardization logic has a gap:
  if unit == 'g' and quantity != 1000:      → normalized to 1kg ✓
  # but: unit == 'g' and quantity == 1000  → falls through → "1000g" ✗
  if unit == 'ml' and quantity != 1000:     → normalized to 1l ✓
  # but: unit == 'ml' and quantity == 1000 → falls through → "1000ml" ✗

  If any store expresses unit price as "per 1000g" or "per 1000ml", you'd get unit_of_measure = "1000g" from one store and "1kg" from another, even
  though they're the same. Looking at the actual Aldi data, Aldi quotes "per 100g" (quantity=100) and "per 1kg" (quantity=1) — both handled
  correctly — so this is an edge case, but it's a real logic gap that could silently produce non-comparable unit prices.

  4. Aldi double-division (already #1 on the todo — just confirming it's real)

  Traced through the actual data: comparison: 168 → DataCleanerAldi divides to 1.68 → PriceNormalizer sees Aldi and divides again to 0.0168 → then
  standardizes to per-100g → final unit_price = 0.000168 instead of 16.80. Off by 10,000x.

  5. Image URLs are captured for Aldi only (i cant remember why i did this but there was a good reason. i think we don't need it for the other companies for somereason. maybe its like you can contruct theres predicatbly but not with aldi.)

  6. IGA unit price relies on string parsing alone

  IGA_FIELD_MAP has "per_unit_price_value": None. So PriceNormalizer falls back to parsing "$3.35/l" or "$1.75/100ml" via regex. This works, but
  it's more fragile than having a numeric value. The raw IGA data actually has unitOfMeasure (size and abbreviation) and priceNumeric — you could
  calculate the unit price directly from those rather than parsing a formatted string.

  ---
  Priority Order for Fixing

  1. Aldi double-division (#1) — data is wrong right now
  ~~2. Woolworths duplicate key — DONE (removed duplicate isHideUnavailableProducts: True, keeping False)~~
  ~~3. IGA sellBy contaminating sizes — DONE (skip appending sellBy when it equals "Each")~~
  ~~4. Aldi fractional kg → g conversion — DONE (product['sizes'] now uses standardized_sizes instead of raw_sizes)~~
  5. Unit price 1000g/1000ml boundary — small edge case but real
