# SplitCart Recommendations

A living to-do list of approved improvements. Items are grouped by area and ordered roughly by priority within each group.

For the separate, larger job of bringing SplitCart onto the shared engineering
policies in `../../freetheplatform/_docs/`, see
[`convergence/README.md`](convergence/README.md). Do not duplicate items
between the two files.

---

## UX — Substitution Flow

- [ ] **Jumpable step indicator** — Currently the only way to go back to a previous substitution item is to click Back repeatedly. Add a clickable step indicator (dots or numbered pills) above the progress bar so users can jump directly to any item they've already seen.

- [ ] **"Review all" list view** — The step-by-step flow is clear for small carts but tedious for large ones. Consider a toggle between the current "one at a time" mode and an "all at once" list view where every item and its substitutes are visible on a single scrollable page. Power users would prefer this.

- [ ] **Running cart summary during substitution** — While working through substitutions the user has no reminder of their full list. A small collapsed header or sidebar showing "12 items in cart · 4 substitutions approved" would provide useful context without taking up space.

- [ ] **Progress bar** — Easy to implement; the one from futureflower can be reused.

---

## UX — Results Page

- [ ] **Explicit "Recommended" label** — The highest-saving tab gets a green badge but users still have to interpret it. Add a clear "Recommended" label to the best-saving tab to remove ambiguity.

- [ ] **Show percentage saving in the panel header** — The savings amount is shown in the tab badge and in the panel as a dollar figure, but the percentage isn't visible inside the panel itself. Showing "You saved 14%" prominently alongside the dollar saving in the panel header would be more satisfying and instantly legible.

---

## Frontend

- [ ] **`isCartSyncing` not set during substitution approvals** — `addItem` and `updateItemQuantity` both set the fetching flag before calling `debouncedSync`. `updateCartItemSubstitution` calls `debouncedSync` but never sets it. No visible UX consequence right now, but inconsistent, and a future guard on that flag would behave differently depending on which path set it. **File:** `frontend/src/context/CartContext.tsx`.

---

## Category System

**Incorrect entries in `pipeline/data/category_mappings.py`.** Several Woolworths mappings are clearly wrong:

- `'Antipasto': 'Non-Alcoholic Drinks'` → should be `'Miscellaneous'` or `None`
- `'Asian Ready Meals': 'Non-Alcoholic Drinks'` → should be `'International'` or `'Deli'`
- `'Board Games & Puzzles': 'Non-Alcoholic Drinks'` → should be `None`

These need a manual audit pass of the full mapping file to catch others like them.

---

## Scraping

- [ ] **Coles category fetching is stalled between two implementations.** `scraping/utils/product_scraping_utils/get_store_specific_categories_coles.py` is a GraphQL-based dynamic fetcher with its own tests, but `scrape.py` calls the hardcoded `get_coles_categories` instead, which itself carries a `TODO: Implement a more robust way` comment. Hardcoding the categories is a real problem; the dynamic version exists but has never run against the live site, so wiring it in means verifying it first, and Coles is the hardest chain to probe.

---

## Pipeline

- [ ] **`print()` calls in `build_price_slots`.** The rest of the codebase passes `command` through for logging. `build_price_slots` uses bare `print()` — these don't reach any log aggregation and can't be suppressed in tests.

- [ ] **`calculate_best_single_company` has an unfinished savings calculation.** `'savings': 0,  # Savings calculation is complex here, maybe compare to baseline?` — the field is in the response contract but is always 0. Either wire it up or remove it from the return value so callers aren't misled.

- [ ] **`CategoryCycleManager` prefetch doesn't fully help.** `prefetch_related('parents')` is applied to the initial queryset, but `_prune_cycles_recursive` then calls `current_node.parents.all()` on nodes that weren't in it — each of those is a fresh query.

- [ ] **`UpdateOrchestrator` is doing too much.** It owns cache-building, file validation, SKU JIT loading, price-cache prep, per-file pipeline orchestration, and post-processing. At ~300 lines it is still readable, but one more feature and it becomes hard to test in isolation. `_is_file_valid` and `_deduplicate_product_data_for_pricing` are fine units; extracting them would thin the orchestrator out.

- [ ] **The two-level price cache is clever but fragile.** `hash_to_pk` and `product_id_to_pk` are constructed by hand in tests and must be kept in sync. A bug once hid in the gap between them — the hash tracks the old identity, the pk tracks the product identity — which is a sign the invariant is enforced nowhere. Worth a comment at minimum.
