# Testing the scraping app

The `scraping` app is the one part of SplitCart whose job is to talk to systems
we do not control. That shapes its tests more than anything else: **no test in
this app makes a network call, and none of them touch the database.** There is
no `@pytest.mark.django_db` anywhere under `scraping/tests/` — the app defines
no models, so there is nothing to persist.

Everything lives in `scraping/tests/util_tests/`. There is no `model_tests/`,
`view_tests/` or `serializer_tests/` layer, because the app has none of those
things.

```
./venv/Scripts/python -m pytest scraping
```

## The rule that matters: patch at the import path, not the library

A scraping test never patches `requests.get`. It patches the name **in the
module under test**, which is the only patch that actually takes effect once
the module has done `import requests` at load time:

```python
with patch('scraping.utils.product_scraping_utils.get_woolworths_categories.requests.get') as mock_get:
```

Every HTTP call site in the app is patched this way — `requests.get` in
`python_file_downloader` and `get_woolworths_categories`, `requests.post` in
each of the four uploaders. `django.conf.settings` is patched the same way, at
the importing module's path rather than globally, so a test can supply an
`API_SERVER_URL` and `INTERNAL_API_KEY` without a real environment.

Scrapers that hold a session are given a mock session rather than a patched
library: `test_product_scraper_woolworths.py` assigns `scraper.session =
MagicMock()` and feeds `session.post.side_effect` a list of canned responses,
which is also how it asserts that pagination stops on an empty page.

If you add a call to an external service, the test for it patches the name
where that module imported it. Anything else silently reaches the internet.

## The four layers

### 1. Field mapping and cleaning — one test module per chain

`test_data_cleaner_woolworths.py`, `test_data_cleaner_coles.py` and
`test_data_cleaner_aldi.py` each feed a raw API payload shaped like that
chain's real response through `DataCleaner{Company}` and assert on the cleaned
dict. `test_base_data_cleaner.py` (27 tests) covers the shared `BaseDataCleaner`
machinery every chain inherits: `_get_value`'s field-map path resolution
including dot notation and list indexing, `_calculate_price_info`'s special /
was-price logic, category-path cleaning, `_get_standardized_unit_price_info`'s
per-100g→per-1kg and per-100ml→per-1L conversions, and the validity guard.

These are the tests that break when a supermarket renames a field, which is the
single most common way a scraper fails in production. Keep the raw fixtures
shaped like the real payload, nested keys and all.

### 2. Normalisation — the identity chain

`test_product_normalizer.py` (30 tests) and `test_size_parser.py`,
`test_size_comparer.py`, `test_price_normalizer.py`, `test_price_hasher.py`
cover the pieces that turn a cleaned product into an identity:
`normalized_brand`, `sizes`, `normalized_name_brand_size`, the standardised
unit price, and the deterministic price hash.

`normalized_name_brand_size` is a database-unique key. A change to the
normaliser that shifts it silently re-partitions the entire product table on
the next ingest, so these tests are load-bearing in a way that their size
suggests. See [`normalized_name_brand_size.md`](normalized_name_brand_size.md)
for what the key is and why it is built that way.

### 3. Cross-chain equivalence — `test_normalization_e2e.py`

The most valuable module in the app. It defines one realistic raw payload per
chain for the _same physical product_, runs each through its own cleaner, and
then asserts in `TestCrossStoreNormalizedKey` that Woolworths, Coles and Aldi
all produce **the same** `normalized_name_brand_size`.

That is the whole product in one assertion: if the three chains disagree on a
product's key, SplitCart cannot compare its price, and the cart split silently
loses an option. Per-chain classes alongside it pin the conversions that get
it there — litres to millilitres, kilograms to grams, multipack extraction,
12-digit barcodes padded to EAN-13, invalid barcodes dropped rather than
stored, and the price hash changing when and only when a price field changes.

When you add a chain, add it here before you add it anywhere else.

### 4. Output and upload — the gate before the server

`test_jsonl_writer.py` pins the commit/cleanup contract: lines go to a temp
file, a successful run moves it into the outbox, a failed one deletes it, and
the in-memory `normalized_name_brand_size` set drops duplicates within a
session. The outbox is never left holding half a scrape.

`test_sanity_checker.py` (19 tests) covers `_validate_product_fields` and
`run_sanity_checks` — the validation that runs over a finished JSONL file
before it is uploaded. A product missing `name`, `price_current` or
`normalized_name_brand_size` is a hard error.

`test_product_uploader.py` covers the uploader's own decisions rather than the
transport: exiting early when the outbox is empty, selecting the latest file
per company, and — the one that matters —
`test_failed_latest_upload_stays_in_outbox`, which drives `requests.post` to
raise `RequestException` and asserts the file is still there afterwards. A
failed upload must never look like a completed one.

## What is not covered

Worth knowing before you assume a green run means more than it does.

- **`ColesSessionManager` has no tests.** It drives Selenium and waits on a
  human to solve a CAPTCHA; there is no useful seam to test it through, and
  nothing pretends otherwise.
- **`product_scraper_coles_v2.py`, `product_scraper_coles_v3.py` and
  `product_scraper_aldi.py` have no scraper-level tests** — only their cleaners
  and category fetchers are covered. `product_scraper_woolworths.py` has one
  test, for category-path stamping.
- **`get_store_specific_categories_coles.py` is tested but not wired into
  production scraping**; `scrape.py` calls `get_coles_categories` instead.

The gap is deliberate at the Selenium boundary and accidental everywhere else.
[`convergence/testing.md`](convergence/testing.md) tracks what is being closed.

## Conventions

- A module-scoped `@pytest.fixture` for the object under test where the cases
  share one (`cleaner`, `writer`), and a module-level builder function
  (`_make_cleaner`, `_make_valid_product`, `_make_jsonl_line`) where each case
  mutates its own copy. Both patterns are in use; pick by which one the case
  needs, not by habit.
- A frozen timestamp (`_TIMESTAMP = datetime(2024, 6, 15)`) wherever a cleaned
  product carries a date, so `scraped_date` is deterministic.
- Empty translation tables (`brand_translations={}`,
  `product_translations={}`) in cleaner tests, so a test asserts what the
  normaliser computes rather than what a 10MB lookup table happens to contain
  today.
- The shared conventions — factories, naming, layer choice — are in
  [`TESTING.md`](TESTING.md) and
  [`../../freetheplatform/_docs/testing-standard-backend.md`](../../freetheplatform/_docs/testing-standard-backend.md).
