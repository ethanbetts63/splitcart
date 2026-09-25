# `ProductBrand`

The brand model is more than a name lookup. It is the anchor for brand identity across supermarkets and feeds the `nnbs` normalization system. A single real-world brand may appear under many names across scraped data; `ProductBrand` consolidates them into one canonical record.

---

## Fields

| Field                        | Type                          | Meaning                                                                          |
| ---------------------------- | ----------------------------- | -------------------------------------------------------------------------------- |
| `name`                       | `CharField`                   | The canonical display name (most common raw form)                                |
| `normalized_name`            | `CharField` (unique, indexed) | Normalized key — bag-of-words, lowercase, no punctuation. The primary identifier |
| `name_variations`            | `JSONField`                   | Raw name strings confirmed to be synonyms of this brand                          |
| `normalized_name_variations` | `JSONField`                   | Normalized versions of `name_variations` — what the translation table reads      |

That is the whole model. It used to carry `confirmed_official_prefix` and `longest_inferred_prefix`, fed by a GS1 Verified-by-GS1 scrape; that subsystem was removed along with the `Store` model and IGA support, and the fields went with it.

---

## How variations are recorded

Variations accumulate via two paths:

**1. Ingestion (`BrandManager`)**

Every ingest pass carries brand pairs discovered from the scraped data. `BrandManager` adds each incoming normalized brand string to the matching `ProductBrand`'s `normalized_name_variations`, creating a new brand row when nothing matches, and bulk-updates only the rows whose variation set actually changed.

**2. Brand reconciliation (`BrandReconciler`)**

After ingestion, `BrandReconciler` reads the current `brand_translation_table.json` and finds any `ProductBrand` DB rows whose `normalized_name` is listed as a variation of another brand. It then:

1. Re-points all `Product.brand` FKs from the duplicate to the canonical brand.
2. Merges the duplicate's variation lists into the canonical brand.
3. Deletes the duplicate row.

This handles cases where a synonym-brand was created as a real brand row before its relationship to a canonical was known.

---

## The brand translation table

**File:** `pipeline/database_updating_classes/product_updating/translation_table_generators/brand_translation_table_generator.py` → writes `pipeline/data/brand_translation_table.json`

The generator reads every `ProductBrand.normalized_name_variations` and produces a flat dict:

```python
BRAND_NAME_TRANSLATIONS = {
    "sanitarium health food company": "sanitarium",
    ...
}
```

`ProductNormalizer` loads this at scrape time and applies it in step 2 of `nnbs` generation — raw brand strings are replaced with the canonical `normalized_name` _before_ the `nnbs` key is computed. This means a correctly identified synonym collapses to the right brand key without ever reaching the DB.

**Circular dependency resolution:** If brand A lists B as a variation and B lists A, a conflict exists. `_resolve_conflict` settles it with a three-tier tiebreaker:

1. Higher product count
2. More recorded variations
3. Alphabetical by name

The loser maps to the winner; the winner's entry is removed from the table so it doesn't point anywhere.

---

## End-to-end loop

```
Ingest → BrandManager records incoming brand strings as name_variations
  └─ BrandTranslationTableGenerator → brand_translation_table.json updated
       └─ [next scrape] ProductNormalizer applies table → correct brand in nnbs
            └─ BrandReconciler → any leftover duplicate brand rows merged + deleted
                 └─ BrandTranslationTableGenerator runs again post-reconciliation
```

Each cycle reduces the number of spurious brand rows and improves `nnbs` accuracy for future scrapes.

---

## Key files

| File                                                                                                                    | Role                                                       |
| ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `products/models/brand.py`                                                                                              | Model definition                                           |
| `pipeline/database_updating_classes/product_updating/brand_manager.py`                                                  | Records incoming brand strings as variations during ingest |
| `pipeline/database_updating_classes/product_updating/post_processing/brand_reconciler.py`                               | Merges duplicate brand DB rows post-ingestion              |
| `pipeline/database_updating_classes/product_updating/translation_table_generators/brand_translation_table_generator.py` | Builds the `variation → canonical` map; resolves conflicts |
| `scraping/utils/product_scraping_utils/product_normalizer.py`                                                           | Applies the brand translation table at scrape time         |
