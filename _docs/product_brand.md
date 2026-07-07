# `ProductBrand`

The brand model is more than a name lookup. It is the anchor for brand identity across supermarkets, feeding both the `nnbs` normalization system and the GS1 prefix system. A single real-world brand may appear under many names across scraped data; `ProductBrand` consolidates them into one canonical record.

---

## Fields

| Field | Type | Meaning |
|---|---|---|
| `name` | `CharField` | The canonical display name (most common raw form) |
| `normalized_name` | `CharField` (unique, indexed) | Normalized key — bag-of-words, lowercase, no punctuation. The primary identifier |
| `name_variations` | `JSONField` | Raw name strings confirmed to be synonyms of this brand |
| `normalized_name_variations` | `JSONField` | Normalized versions of `name_variations` — what the translation table reads |
| `confirmed_official_prefix` | `CharField` (nullable) | GS1 license key scraped from Verified-by-GS1. Authoritative — ground truth |
| `longest_inferred_prefix` | `CharField` (nullable) | Best-guess prefix from longest common prefix (LCP) analysis of barcodes. Not yet wired into the pipeline |

---

## How variations are recorded

Variations accumulate via two paths:

**1. GS1 ingestion (`GS1UpdateOrchestrator`)**

When a GS1 scrape confirms a prefix for a brand, the orchestrator searches for all products whose barcode starts with that prefix but are linked to a *different* brand. Those mismatched brand names are recorded as `name_variations` / `normalized_name_variations` on the canonical brand. The canonical brand is defined by the GS1 company name, not by whatever Woolworths or Coles happened to call it.

**2. Brand reconciliation (`BrandReconciler`)**

After ingestion, `BrandReconciler` reads the current `brand_translation_table.py` and finds any `ProductBrand` DB rows whose `normalized_name` is listed as a variation of another brand. It then:
1. Re-points all `Product.brand` FKs from the duplicate to the canonical brand.
2. Merges the duplicate's variation lists into the canonical brand.
3. Deletes the duplicate row.

This handles cases where a synonym-brand was created as a real brand row before its relationship to a canonical was known.

---

## The brand translation table

**File:** `pipeline/.../brand_translation_table_generator.py` → writes `data/brand_translation_table.py`

The generator reads every `ProductBrand.normalized_name_variations` and produces a flat dict:

```python
BRAND_NAME_TRANSLATIONS = {
    "sanitarium health food company": "sanitarium",
    ...
}
```

`ProductNormalizer` loads this at scrape time and applies it in step 2 of `nnbs` generation — raw brand strings are replaced with the canonical `normalized_name` *before* the `nnbs` key is computed. This means a correctly identified synonym collapses to the right brand key without ever reaching the DB.

**Circular dependency resolution:** If brand A lists B as a variation and B lists A, a conflict exists. The generator resolves it with a four-tier tiebreaker:

1. Has `confirmed_official_prefix` (GS1 wins)
2. Higher product count
3. More recorded variations
4. Alphabetical by name

The loser maps to the winner; the winner's entry is removed from the table so it doesn't point anywhere.

---

## End-to-end loop

```
GS1 scrape → confirmed prefix set on canonical brand
  └─ Products with prefix but wrong brand → name_variations recorded
       └─ BrandTranslationTableGenerator → brand_translation_table.py updated
            └─ [next scrape] ProductNormalizer applies table → correct brand in nnbs
                 └─ BrandReconciler → any leftover duplicate brand rows merged + deleted
```

Each cycle reduces the number of spurious brand rows and improves `nnbs` accuracy for future scrapes.

---

## Key files

| File | Role |
|---|---|
| `products/models/brand.py` | Model definition |
| `pipeline/database_updating_classes/gs1_update_orchestrator.py` | Records variations from GS1 prefix matches |
| `pipeline/.../brand_reconciler.py` | Merges duplicate brand DB rows post-ingestion |
| `pipeline/.../brand_translation_table_generator.py` | Builds `variation → canonical` map; resolves conflicts |
| `scraping/utils/product_scraping_utils/product_normalizer.py` | Applies brand translation table at scrape time |
| `pipeline/management/commands/infer_and_reconcile_brands.py` | LCP-based prefix inference (standalone, not yet in pipeline) |
