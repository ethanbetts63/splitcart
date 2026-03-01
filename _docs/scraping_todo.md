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

  5. save_to_inbox.py — Has no .pyc file, is not imported anywhere in the codebase. It writes individual UUID-named JSON files to
  scraping/data/inboxes/product_inbox/, a path that nothing reads. This path doesn't even appear in the pipeline. Completely orphaned.

  6. get_store_specific_categories_coles.py — A GraphQL-based dynamic category fetcher. Has no .pyc, is never imported. The dynamic approach was
  written but never wired in. Meanwhile get_coles_categories.py has a TODO: Implement a more robust way comment. These two files exist in a stalled
  state — the solution exists but was never connected.

  7. atomic_scraping_utils.py::append_to_temp_file — The function at line 6 is dead. The only other function (finalize_scrape) is used by
  JsonlWriter.commit(). The file itself survives on that one use.

  8. JsonlWriter.finalize() method (jsonl_writer.py:73) — Described as "maintained for backward compatibility" but nothing calls it.
  base_product_scraper.py calls close() + commit() / cleanup() directly. Dead.

  9. ProductScraperAldi.post_scrape_enrichment (product_scraper_aldi.py:98-102) — Overrides the base class method with just pass. The base class
  default is also pass. The override is pure noise.

  10. --woolworths2 flag in find_stores.py — The argument is registered (parser.add_argument('--woolworths2', ...)) but the handle() method has no
  if options['woolworths2'] branch. It does nothing.

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

  22. base_product_scraper.py uses print() (base_product_scraper.py:24)
  print("Setup failed, aborting scrape.") — everything else in the file uses self.command.stdout/stderr.write(...). This message would not appear in
   Django's log output.

  23. BargainUploader doesn't archive (inconsistent with Gs1Uploader, StoreUploader)
  Gs1Uploader and StoreUploader move files to an archive directory after upload. BargainUploader and CategoryLinksUploader just delete them.
  SubstitutionsUploader also just deletes. No consistent policy.

  24. PascalCase module filenames (DataCleanerAldi.py, BaseDataCleaner.py, etc.)
  Python convention is snake_case for module filenames. All other utils in the codebase use lowercase. This is a cosmetic inconsistency but causes
  slightly awkward imports.

  25. ScraperOutput.update_progress() — manual max logic (output_utils.py:18-19)
  self.categories_scraped = categories_scraped if categories_scraped > self.categories_scraped else self.categories_scraped
  This is just max(). Not wrong, but harder to read than necessary.

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
