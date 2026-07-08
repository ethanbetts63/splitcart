# Node Category Assignment Task

## What you are doing and why

Splitcart is an Australian grocery price comparison platform. It scrapes product data from four supermarkets: **Coles**, **Woolworths**, **Aldi**, and **IGA**. Each supermarket has its own category hierarchy, and their category node names often differ (e.g. "Yoghurt" vs "Yoghurt" — same, "Dairy, Eggs & Fridge" vs "Dairy & Fridge" — same concept).

To support user browsing (filtering products by category on the site), each product needs a **primary category** — a clean, cross-company label like "Yogurt", "Milk", "Snacks".

Your job is to assign each canonical category node in `node_assignment_candidates.jsonl` to a primary category, or explicitly exclude it. Every entry you classify is permanently recorded and will never be shown to you again.

---

## How canonical slugs are generated

Supermarket category paths have been cross-company equivalenced — e.g. "Dairy, Eggs & Fridge" (Woolworths) and "Dairy & Fridge" (Coles) are recognised as the same concept and share the canonical slug `dairy-eggs-fridge`. For nodes not yet equivalenced, the canonical slug is just the slugified node name.

When a product is scraped, PathClassifier walks its category path from leaf (most specific) to root and assigns the first matching primary category. Your assignments are what it finds.

---

## The file format

Each line of `node_assignment_candidates.jsonl` is a JSON object:

```json
{
  "canonical_slug": "yoghurt",
  "evidence_count": 4521,
  "companies": ["Woolworths", "Coles"],
  "raw_names": [
    {"company": "Woolworths", "name": "Yoghurt"},
    {"company": "Coles", "name": "Yoghurt"}
  ],
  "path_types": ["canonical_taxonomy"],
  "sample_paths": [
    "Dairy, Eggs & Fridge > Yoghurt > Greek Yoghurt (Woolworths)"
  ]
}
```

Fields:
- `canonical_slug` — the key you're assigning. Use this when calling `assign_node_category`.
- `evidence_count` — number of path-entry observations across all products. Higher = more common.
- `companies` — which supermarkets have this node.
- `raw_names` — the actual node name strings that map to this canonical slug (useful for understanding what it means).
- `path_types` — taxonomy types observed: `canonical_taxonomy` (real browse hierarchy), `seasonal`, `promotion`, `dietary`, `brand_collection`, `merchandising`, `unknown`.
- `sample_paths` — example full paths showing where this node appears in context.

---

## Valid primary categories

Assign each node to exactly one of these slugs, or use `none` to exclude it:

| Slug | Description |
|------|-------------|
| `alcoholic-drinks` | Beer, wine, spirits, cider |
| `baby` | Nappies, formula, baby food, wipes |
| `bakery` | Bread, rolls, pastries, cakes |
| `beauty` | Skincare, haircare, cosmetics, personal care |
| `beef` | Beef and veal cuts |
| `cheese` | All cheese varieties |
| `chicken` | Chicken and poultry cuts |
| `chocolate` | Chocolate blocks, bars, boxes |
| `cleaning` | Household cleaning, laundry, dishwashing |
| `dairy` | General dairy (cream, butter, margarine) |
| `deals` | Promotional pricing categories (Down Down, etc.) |
| `deli` | Deli meats, ready meals, fresh prepared food |
| `eggs` | Eggs |
| `freezer` | Frozen goods (meals, vegetables, pastry, pizza) |
| `fruit` | Fresh and dried fruit, nuts |
| `garden` | Garden, outdoor, pest control |
| `health` | Vitamins, medicines, personal health, oral care |
| `health-foods` | Health foods, sports nutrition, organic staples |
| `home` | Homewares, kitchen, stationery, clothing |
| `ice-cream` | Ice cream tubs, sticks, gelato |
| `international` | International and world foods |
| `lamb` | Lamb cuts and mince |
| `lollies` | Lollies, licorice, gum, mints |
| `meat` | General/mixed meat, game, turkey |
| `milk` | Fresh, long-life, flavoured, plant-based milks |
| `miscellaneous` | Catch-all for things that don't fit elsewhere |
| `non-alcoholic-drinks` | Soft drinks, juice, water, cordials, energy drinks |
| `pantry` | Dry goods, canned food, pasta, rice, spreads, condiments |
| `pet` | Pet food and accessories |
| `pork` | Pork, bacon, ham, salami |
| `seafood` | Fresh, frozen, and canned seafood |
| `sauces` | Sauces, condiments, dressings, relish |
| `snacks` | Chips, crackers, savoury snacks, biscuits |
| `spices` | Herbs, spices, seasonings, fresh herbs |
| `sweets` | General sweets, desserts, cakes |
| `veg` | Fresh and prepared vegetables, salads |
| `yogurt` | All yoghurt varieties |
| `none` | Explicitly exclude — node should not map to any primary category |

---

## Assignment guidelines

**Assign to the most specific matching category.** If the node is "Yoghurt", assign `yogurt` — not `dairy`. PathClassifier scans leaf-to-root, so a specific leaf assignment correctly overrides a more general ancestor.

**Use `none` for:**
- Seasonal/promotional overlays: Christmas, Easter, Down Down, Specials, Limited Time Only, Big Night In, etc.
- Ambiguous root nodes that are too broad to assign: "Meat & Seafood", "Dairy, Eggs & Fridge", "Drinks" (when used as a root that contains both alcoholic and non-alcoholic).
- Non-food categories that don't fit any slot: collectables, toys, stationery (unless they clearly map to `home`).
- Brand collection roots: Cadbury, Heinz, Nescafe at the root level (the sub-nodes will be classified separately).

**Use `miscellaneous` sparingly** — only for genuinely uncategorisable grocery items that are clearly real products. When in doubt between two valid categories, pick the closer one.

**`path_types` is your signal:**
- `canonical_taxonomy` only → this is a real browse node, assign a category or use `none` if it's a broad root.
- `seasonal` or `promotion` only → almost always `none`.
- Mixed types → the `canonical_taxonomy` usage should guide your decision.

**evidence_count matters:**
- High evidence (100+) → node is common, get it right.
- Low evidence (< 5) → may be a rare or one-off node; `none` is acceptable if genuinely ambiguous.

---

## How to record your decision

For each entry, call:

```
python manage.py assign_node_category <canonical_slug> <primary_category_slug|none>
```

With an optional note:

```
python manage.py assign_node_category dairy-eggs-fridge none --note "Root node, too broad — leaf nodes classified individually"
```

The entry is immediately removed from `node_assignment_candidates.jsonl` and archived in `node_assignment_decisions.jsonl`. You will never see it again.

Work through the file from top to bottom — highest evidence first, so the most impactful decisions come early.

---

## After you finish

Once all candidates are classified, run:

```
python manage.py apply_node_category_assignments
python manage.py generate --primary-cats
```

This rebuilds `canonical_category_assignments.json` and propagates the assignments to all products.

---

## Scope

Classify every entry in the file. Do not skip any. If a node is genuinely ambiguous, use `none` with a note — that is a valid decision. When you finish, the candidates file will be empty.
