# SplitCart Substitution System

This document covers the full lifecycle of substitutions — from offline generation to the cart approval flow.

---

## Overview

Substitutions exist at two levels:

- **`ProductSubstitution`** — a static, scored relationship between two products (e.g. "Brand A milk ↔ Brand B milk"). Generated offline and stored in the database.
- **`CartSubstitution`** — a per-user instance of a `ProductSubstitution`, attached to a specific `CartItem`. Holds the user's `is_approved` flag and an adjustable quantity.

---

## Generation Pipeline

Substitutions are generated locally and loaded to the server. The three commands involved are:

```bash
python manage.py generate --subs --dev   # local: runs generators, writes to outbox
python manage.py upload --subs --dev     # local: uploads outbox JSON to server inbox
python manage.py update --subs           # server: reads inbox, writes to DB
```

### Generator Flow

```
SubstitutionsGenerator.run()
  │
  ├─ Fetches products, categories, category_links from server API
  │
  ├─ Lvl1SubGenerator   → same brand + name, different size (score: 1.0)
  ├─ Lvl2SubGenerator   → same brand, fuzzy name match (token_set_ratio > 90), same size (score: 0.95)
  ├─ Lvl3SubGenerator   → same primary category, cosine similarity > 0.75 (score: similarity)
  └─ Lvl4SubGenerator   → linked categories (via CategoryLinks graph), cosine similarity > 0.75
  │
  └─ Writes combined list → data_management/data/outboxes/substitutions_outbox/substitutions.json
```

LVL3 and LVL4 use a `SentenceTransformer` (`all-MiniLM-L6-v2`) to encode product names into embeddings and compute cosine similarity. LVL4 uses a DFS traversal over the `CategoryLinks` graph to build "super-groups" of related categories, then cross-matches products between them (excluding pairs that already qualify as LVL3).

### DB Load

`update --subs` runs `SubstitutionUpdateOrchestrator`, which reads the JSON and bulk-creates or updates `ProductSubstitution` rows. The relationship is symmetric — a pair `(A, B)` is enforced as unique.

---

## Data Models

```
ProductSubstitution
  ├─ product_a          FK → Product
  ├─ product_b          FK → Product
  ├─ level              LVL1 | LVL2 | LVL3 | LVL4
  └─ score              float 0.0–1.0  (1.0 = exact size match, < 1.0 = semantic)

CartSubstitution
  ├─ id                 UUID
  ├─ original_cart_item FK → CartItem  (related_name: chosen_substitutions)
  ├─ substituted_product FK → Product
  ├─ quantity           int  (adjustable — useful when pack sizes differ)
  └─ is_approved        bool (default: False)
```

---

## Runtime Flow

When a user adds an item to their cart, the sync endpoint creates `CartSubstitution` records immediately so they are ready by the time the user reaches the substitution page.

```
User adds product to cart
  │
  ▼
POST /api/carts/sync/
  ├─ Creates new CartItems (bulk_create)
  ├─ Resolves cart.selected_store_list (lazy-links from user's active list if not set)
  └─ For each new CartItem:
       │
       ▼
       SubstituteManager(product_id, store_ids)
         ├─ get_pricing_stores_map(store_ids)  → translates member IDs to anchor IDs
         │   (Price rows only exist on anchor stores; member store prices are deleted
         │    after group confirmation — see group_maintenance/README.md)
         ├─ Finds up to 5 ProductSubstitution rows where substitute has prices at
         │   the resolved anchor stores
         └─ Creates CartSubstitution for each (is_approved=False, quantity=1)
  │
  ▼
Cart response includes items[].substitutions[]
```

The product page also exposes substitutes directly via `GET /api/products/<id>/substitutes/` (6-hour cache). That endpoint does not filter by store — it shows all known substitutes for discovery purposes.

---

## User Interaction

The substitution flow sits between "Add to Cart" and the final optimization.

```
User clicks "Next" from cart
  │
  ▼
/substitutions
  ├─ Filters cart items to those where substitutions.length > 0
  ├─ If none → auto-skips to /final-cart (optimization runs immediately)
  └─ For each item with substitutes:
       ├─ Left panel: original product
       └─ Right panel: up to 5 substitute candidates (scrollable)
            ├─ "Approve" button  → PATCH …/substitutions/{id}/  { is_approved: true }
            ├─ Quantity stepper  → visible after approval, PATCH with new quantity
            │   (allows adjusting e.g. 1×1L → 2×500mL)
            └─ Approved indicator (green border + badge)
  │
  ├─ "Next" → advance to next item
  ├─ "Approve All & Split" → approves all on current item, then splits
  └─ "Skip all substitutions" → goes straight to optimization with original items
  │
  ▼
User clicks "Split my Cart!"
  │
  ▼
POST /api/carts/{id}/optimize/
  └─ Approved substitutes replace their original item in the optimizer's price slots
     (if no substitutes approved for an item, the original product is used)
```

Substitution approval is an optimistic update — the UI reflects the change immediately while the PATCH request runs in the background, with rollback on failure.

---

## Design Notes

- **Why anchors matter for substitution filtering**: The group system deletes `Price` rows from member stores once confirmed as matching the anchor. `SubstituteManager` must call `get_pricing_stores_map()` to resolve the user's selected stores to their anchor IDs before querying; otherwise the store filter returns zero results.
- **Approved substitutes replace, not supplement**: In the optimizer, if any substitute is approved for a cart item, the original product is dropped from that slot entirely. The optimizer only sees the approved substitutes for that item.
- **Quantity matters**: A user can approve a substitute at a different quantity (e.g. approving 2×500mL when the original was 1×1L). This quantity is what the optimizer uses.
- **LVL1 and LVL2 require the same brand** — they cover size and naming variants within a brand. LVL3 and LVL4 cross brand boundaries using semantic similarity.
