# `ProductPriceSummary`

A pre-computed, one-to-one snapshot of aggregated price metrics for a single product. Its sole purpose is to make bargain discovery fast at query time without scanning the full `Price` table on every request.

**Model:** `products/models/product_price_summary.py`

| Field | Type | Description |
|---|---|---|
| `product` | OneToOneField (PK) | The product this summary belongs to |
| `min_price` | Decimal | Cheapest current price across all stores |
| `max_price` | Decimal | Most expensive current price across all stores |
| `company_count` | PositiveInt (indexed) | Number of distinct companies that stock this product |
| `iga_store_count` | PositiveInt | Number of distinct IGA stores that stock it |
| `best_possible_discount` | Int (indexed) | `((max − min) / max) × 100`, rounded down |

---

## Why it exists

Bargain queries need to sort thousands of products by cross-store price variance. Doing that live — joining `Product → Price → Store → Company` and aggregating on the fly — is too expensive at request time. `ProductPriceSummary` pre-computes those aggregates so the bargain carousel can do a single indexed scan to find candidates, then verify a small shortlist against live prices.

---

## How it is generated

**File:** `data_management/utils/generation_utils/price_summaries_generator.py`
**Trigger:** `generate --price-summaries` (run after each product ingestion)

The generator fully rebuilds all summaries on each run (delete then recreate in 5000-row chunks). A summary is only created for a product if **all** of these are true:

1. The product has **≥ 2 prices** in the DB
2. `min_price ≠ max_price` (there is actually a price difference)
3. The product is stocked by **≥ 2 companies**, OR by **≥ 2 IGA stores** (IGA is store-by-store priced, so two IGA stores count as meaningful variance)
4. `best_possible_discount` is between **5% and 70%** (filters out noise below 5% and implausibly large gaps above 70%)

---

## The two-step bargain query pattern

`ProductPriceSummary` is not the final answer — it is a pre-filter. Because it is computed globally (all stores), it can surface products that look like bargains globally but aren't relevant to *this* user's selected stores. The query pattern used throughout the codebase is:

**Step 1 — Cheap indexed scan on summaries (candidate selection)**
Filter `ProductPriceSummary` by `best_possible_discount`, `company_count`, and whether the product has prices at the user's anchor stores. Take the top ~200 candidates ordered by `-best_possible_discount`.

**Step 2 — Live verification in memory**
Fetch actual `Price` rows for just those candidates, restricted to the user's anchor stores. Recalculate the real discount for the user's specific store set. Sort and return.

This keeps the expensive per-user calculation to a small, already-promising candidate pool.

**Files using this pattern:**
- `products/views/bargain_carousel_view.py` — homepage bargain carousel
- `products/utils/product_ordering.py` — `get_bargain_first_ordering()` for product list pages

---

## IGA special-casing

IGA stores are not grouped into anchors the way Coles/Woolworths are — each IGA store is independently priced. A product that appears at two IGA stores at different prices is a genuine bargain opportunity. `iga_store_count` exists specifically to catch this case: a product stocked by only one company (IGA) but at two+ stores with price variance still qualifies for a summary.

---

## Key files

| File | Role |
|---|---|
| `products/models/product_price_summary.py` | Model definition |
| `data_management/utils/generation_utils/price_summaries_generator.py` | Builds all summaries |
| `products/views/bargain_carousel_view.py` | Homepage bargain carousel (24h cached) |
| `products/utils/product_ordering.py` | Bargain-first ordering for product list pages |
