
  Writers (generate the file format):
  1. base_translation_table_generator.py — write_to_file() uses pformat, writes .py

  Loaders (read the file format):
  2. BaseDataCleaner._load_translation_table(path) — the core loader, split('=') + ast.literal_eval
  3. BaseDataCleaner._load_translation_tables() — calls above with hardcoded .py paths
  4. brand_reconciler._load_translation_table() — wraps #2
  5. product_reconciler._load_translation_table() — wraps #2

  HTTP transfer (file name + path hardcoded as .py):
  6. scrape.py:_fetch_translation_tables() — hardcodes .py destination paths, calls downloader
  7. python_file_downloader.fetch_python_file() — downloads and saves; format-agnostic but filename passed in
  8. base_python_file_view.py — reads file from disk, serves raw as text/plain
  9. brand_translation_file_view.py / product_translation_file_view.py — configure the above view

  Consumers (receive the dicts, no file I/O — no changes needed):
  - base_product_scraper.py — loads via BaseDataCleaner._load_translation_tables()
  - product_normalizer.py — accepts dicts as arguments
  - All 4 DataCleaner*.py classes — pass through to ProductNormalizer
  - All 4 scrapers (coles_v2, coles_v3, aldi, iga, woolworths) — pass dicts down

  Tests that touch the file format directly (need _write_translation_table helper updated):
  10. test_brand_reconciler.py
  11. test_product_reconciler.py
  12. test_translation_table_generators.py
  13. test_python_file_downloader.py — tests the downloader; mocks responses so file content matters

  ---