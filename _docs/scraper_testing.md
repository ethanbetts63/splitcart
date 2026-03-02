---
  Testing Strategy

  Two distinct goals:

  Goal 1: Correctness — the data comes out exactly how we expect

  Goal 2: Drift detection — if a store changes their API structure, we catch it immediately

  ---
  Goal 1: Correctness Tests (E2E Normalization)

  This is the core of what you want. The approach:

  - Use real API responses as fixtures — you already have the raw_*.txt files, you'll want to expand them with more varied cases
  - Run each store's full DataCleaner pipeline on the fixture
  - Assert exact output values for every field that matters

  For each store you want to cover:
  - A normal product (no special, has all fields)
  - A product on special (was_price logic)
  - A product with a multipack size (e.g. 6 x 375ml)
  - A product where size is in kg not g (the 0.11kg → 110g conversion)
  - A product with no brand
  - A product with no barcode (or invalid barcode)
  - A product with a complex category path

  The assertions should be exact — not "unit_price is not None" but unit_price == 16.80. These tests are your specification. When they pass, you
  know the data is correct. When they fail, you know exactly what broke.

  For the normalized_name_brand_size key specifically, you want cross-store tests — take the same product from two different chains, run both
  through their respective cleaners, and assert the keys match. That's the highest-value test in the whole suite because it validates the core value
   proposition of the system.

  ---
  Goal 2: Drift Detection (Schema Contract Tests)

  This is harder and most people don't think about it until a scraper silently breaks. The idea is to define what you expect the raw API response to
   look like and fail loudly if reality diverges.

  The approach: for each store, write a test that takes a raw API response and validates:
  1. Field presence — every field in the field_map has a corresponding key somewhere in the raw response
  2. Type correctness — price_current is numeric, name is a string, onlineHeirs is a list
  3. Value ranges — price is > 0, sizes are strings matching expected patterns

  When Coles changes pricing.now to pricing.currentPrice, the field presence test fails immediately and tells you exactly which field disappeared.
  Without this, you'd just silently get None prices for all Coles products until someone noticed.

  The practical implementation: a small validator per store that runs as part of the test suite. You run it against the saved fixtures to confirm it
   passes, then when you update fixtures with fresh real data periodically, drift shows up as test failures.

  ---
  Structure

  Given your existing test structure from TESTING.md:

  scraping/
  └── tests/
      ├── __init__.py
      ├── fixtures/
      │   ├── raw_woolworths.json
      │   ├── raw_coles.json
      │   ├── raw_aldi.json
      │   └── raw_iga.json
      └── util_tests/
          ├── test_product_normalizer.py   ← unit tests: sizes, brand, barcode, dedup key
          ├── test_price_normalizer.py     ← unit tests: unit price extraction, measure parsing
          ├── test_price_hasher.py         ← unit tests: determinism, field sensitivity
          ├── test_jsonl_writer.py         ← unit tests: dedup, commit, cleanup
          ├── test_data_cleaner_woolworths.py  ← E2E: full pipeline on fixtures
          ├── test_data_cleaner_coles.py
          ├── test_data_cleaner_aldi.py
          ├── test_data_cleaner_iga.py
          └── test_schema_contracts.py     ← drift detection: field presence + types per store

