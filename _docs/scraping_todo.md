  ---

  3. BaseStoreScraper infinite recursion (base_store_scraper.py:60-64)
  except Exception as e:
      ...
      time.sleep(10)
      self.run()  # recursive with no limit
  Any persistent error (API change, auth failure) causes infinite recursion and eventual stack overflow. There's no retry counter or bail-out.

  6. get_store_specific_categories_coles.py — A GraphQL-based dynamic category fetcher. Has no .pyc, is never imported. The dynamic approach was
  written but never wired in. Meanwhile get_coles_categories.py has a TODO: Implement a more robust way comment. These two files exist in a stalled
  state — the solution exists but was never connected.

  12. Stale .pyc files for deleted sources: __pycache__ contains barcode_scraper_coles.cpython-312.pyc and product_scraper_coles.cpython-312.pyc —
  both V1 scrapers deleted and replaced by V2 — but the compiled bytecode remains.

  20. IGA company name lowercase mismatch (scrape_barcodes.py:25 vs rest of pipeline)
  ColesBarcodeScraperV2 hardcodes self.company = "coles" (lowercase). Every other path gets the company name from store.company.name in the DB (e.g.
   "Coles" with capital). PriceNormalizer does self.company.lower() == 'aldi', so the case doesn't matter there. But metadata written to JSONL files
   from the barcode scraper would have "coles" lowercase while regular scrapes write "Coles". The ingestion pipeline may be case-insensitive enough
  that this doesn't break anything, but it's inconsistent.






