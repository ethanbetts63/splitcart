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
  ├─ Fetches the product list from /api/export/products/ (nothing else)
  │
  ├─ Lvl1SubGenerator   → same brand + name, different size (score: 1.0)
  ├─ Lvl2SubGenerator   → same brand, fuzzy name match (token_set_ratio > 90), same size (score: 0.95)
  ├─ Lvl3SubGenerator   → same primary category, cosine similarity > 0.75 (score: similarity)
  └─ Lvl4SubGenerator   → sibling slugs within a PRIMARY_CATEGORY_HIERARCHY super-group, cosine similarity > 0.75
  │
  └─ Writes combined list → pipeline/data/outboxes/substitutions_outbox/substitutions.json
```

LVL3 and LVL4 use a `SentenceTransformer` (`all-MiniLM-L6-v2`) to encode product names into embeddings and compute cosine similarity. LVL4 builds its "super-groups" from `PRIMARY_CATEGORY_HIERARCHY` via `_build_slug_super_groups()` — a parent's children are one group — then cross-matches products between them, excluding pairs that already qualify as LVL3. It used to traverse the `CategoryLink` graph; that approach was replaced, and the generator's own docstring says so.

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
  └─ For each new CartItem:
       │
       ▼
       SubstituteManager(product_id, company_ids=get_default_company_ids())
         ├─ Finds up to 5 ProductSubstitution rows where the substitute has
         │   prices at one of those companies
         └─ Creates CartSubstitution for each (is_approved=False, quantity=1)
  │
  ▼
Cart response includes items[].substitutions[]
```

The product page also exposes substitutes directly via `GET /api/products/<id>/substitutes/` (6-hour cache). That endpoint applies no company filter at all — it shows every known substitute, for discovery rather than for pricing.

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

- **The company filter is global, not per user**: `SubstituteManager` is constructed with `get_default_company_ids()`. `Cart` carries no store or company selection field, and there is no per-user store list — Coles, Woolworths and Aldi all price nationally, so there is nothing for a user to pick.
- **Approved substitutes replace, not supplement**: In the optimizer, if any substitute is approved for a cart item, the original product is dropped from that slot entirely. The optimizer only sees the approved substitutes for that item.
- **Quantity matters**: A user can approve a substitute at a different quantity (e.g. approving 2×500mL when the original was 1×1L). This quantity is what the optimizer uses.
- **LVL1 and LVL2 require the same brand** — they cover size and naming variants within a brand. LVL3 and LVL4 cross brand boundaries using semantic similarity.
