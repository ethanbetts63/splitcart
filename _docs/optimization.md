# Cart Optimization

The optimizer finds the cheapest way to split a user's shopping list across multiple supermarkets, accounting for substitutes, delivery, and a configurable store limit.

---

## Algorithm

**File:** `data_management/utils/cart_optimization/calculate_optimized_cost.py`

The solver uses **linear programming (PuLP / CBC)**. It models the cart as a set of "slots" — one per cart item — each with a list of purchasable options across stores.

**Decision variables:**
- `choice_vars[(slot, option)]` — binary: is this option chosen?
- `store_usage[store_id]` — binary: is this store used at all?

**Objective:** minimise `sum(option.price × quantity × choice_var)`

**Constraints:**
1. Exactly one option chosen per slot (every item must be fulfilled)
2. An option can only be chosen if its store is marked as used
3. Total stores used ≤ `max_stores` (user-configurable, e.g. 2, 3, 4)
4. Each product ID chosen at most once across all slots (prevents double-counting)

The optimizer is run separately for each `max_stores` value, and in parallel for two cart variants: **with approved substitutes** and **without** (original items only). This gives the frontend a range of plans to present.

---

## Input: Price Slots

**File:** `data_management/utils/cart_optimization/build_price_slots.py`

A slot is a list of all purchasable options for one cart item. If the user has approved substitutes for an item, those substitutes *replace* the original in the slot entirely — the original product is dropped.

Prices are queried only for the user's selected stores. Because national chains use an anchor/member store grouping system, member store IDs are first resolved to their anchor before any price query (see `store_grouping.md`).

---

## Baseline & Savings

**File:** `data_management/utils/cart_optimization/calculate_baseline_cost.py`

Baseline = average price per slot across all available stores, summed over all slots. It represents the cost of picking randomly rather than optimally.

```
Savings = baseline_cost − optimized_cost
```

The baseline is the same for both the with-substitutes and without-substitutes paths, so the two savings figures are directly comparable.

---

## Substitutions

**Files:** `data_management/utils/cart_optimization/substitute_manager.py`, `products/models/substitution.py`

Substitutes expand the solution space. More options per slot = more flexibility for the optimizer to route each item to the cheapest store.

Substitutes are matched at scrape/generation time and stored as `ProductSubstitution` rows with a score (0–1). At cart-sync time, up to 5 substitutes per item are surfaced as `CartSubstitution` records. The user approves or rejects them before optimization runs.

| Level | Match type |
|---|---|
| LVL1 | Same brand + name, different size |
| LVL2 | Same brand, fuzzy name match (>90%), same size |
| LVL3 | Same primary category, semantic similarity >0.75 |
| LVL4 | Linked category, semantic similarity >0.75 |

LVL3/4 use SentenceTransformer embeddings (`all-MiniLM-L6-v2`).

---

## Savings Potential Factors

These are the factors that determine how much a user can actually save:

### Expand savings potential

| Factor | Why |
|---|---|
| **Product commonality across companies** | The more products two stores share, the more slots the optimizer can route to whichever is cheaper. This is the single biggest lever. |
| **Cross-company substitutes** | If an exact match doesn't exist, an approved substitute gives the optimizer a cross-company option it wouldn't otherwise have. Without substitutes you are forcing the user to say for example "I will only have devondale milk", whereas in reality they almost certainly would be just as happy with many other brands and sizes.|
| **Internal substitutes (same brand, different size)** | LVL1/2 substitutes within the same company add options and let the optimizer exploit unit-price differences. |
| **Price variance between companies** | Wide gaps (e.g. Aldi vs Coles) mean more to gain from routing. Tight gaps (Coles vs Woolworths on staples) limit opportunity. |
| **More stores in the calculation** | Each additional store added to `max_stores` opens more routing options. Diminishing returns past ~3 stores. |

### Limit savings potential

| Factor | Why |
|---|---|
| **Niche products** | Specialty items are less likely to have equivalents in other stores' ranges and less likely to have approved substitutes. The optimizer is forced to use whichever store carries them. |
| **All selected stores belong to the same price group** | If the user picks stores that share an anchor (same pricing), the optimizer has no real choice between them. |
| **Rejected substitutes** | The optimizer only sees what the user approves. Declining all substitutes caps savings at whatever cross-store spread exists on the exact original products. |
| **Low cart commonality** | A basket of common staples (milk, bread, eggs) has high cross-company overlap. A basket of specialty items does not. |

---

## Key files

| File | Role |
|---|---|
| `data_management/utils/cart_optimization/calculate_optimized_cost.py` | LP solver — core algorithm |
| `data_management/utils/cart_optimization/build_price_slots.py` | Converts cart + prices into optimizer input |
| `data_management/utils/cart_optimization/calculate_baseline_cost.py` | Average-price baseline |
| `data_management/utils/cart_optimization/calculate_best_single_store.py` | Best single-store fallback |
| `data_management/utils/cart_optimization/substitute_manager.py` | Finds substitutes for cart items |
| `users/utils/cart_optimization.py` | Orchestrates both optimization paths |
| `products/models/substitution.py` | `ProductSubstitution` model |
| `users/models/cart_substitution.py` | Per-user approved substitutes |
