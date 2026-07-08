# Category Suspect Classification Task

## What you are doing and why

Splitcart is an Australian grocery price comparison platform. It scrapes product data from four supermarkets: **Coles**, **Woolworths**, **Aldi**, and **IGA**. Each supermarket has its own category hierarchy — the same product might appear under "Dairy, Eggs & Fridge → Milk → Full Cream Milk" at Woolworths and "Dairy & Fridge → Fresh Milk → Full Cream" at Coles.

To match products across companies, we need to know which category nodes from different companies refer to the same concept. For example: does "Dairy, Eggs & Fridge" (Woolworths) mean the same thing as "Dairy & Fridge" (Coles)? If yes, we can normalize them to the same canonical slug and use that to group equivalent products cross-company.

Your job is to classify each entry in `category_suspects.jsonl` as a match, not a match, or unsure. Every entry you classify is permanently recorded and will never be shown to you again.

---

## How the suspects are generated

When a product has category paths from multiple companies simultaneously, we align the paths from the leaf (most specific node) upward and pair each node level-for-level. For example:

```
Woolworths path: ["Dairy, Eggs & Fridge",  "Yoghurt",  "Greek Yoghurt"]
Coles path:      ["Dairy & Fridge",         "Yoghurt",  "Greek Style Yoghurt"]

depth_from_leaf 0 (leaf):  "Greek Yoghurt"    ↔  "Greek Style Yoghurt"
depth_from_leaf 1:         "Yoghurt"           ↔  "Yoghurt"
depth_from_leaf 2 (root):  "Dairy, Eggs & Fridge" ↔ "Dairy & Fridge"
```

Each unique cross-company node pair at a given depth becomes one suspect entry. The `evidence_count` tells you how many products produced this pairing. High evidence means many products were seen in both paths simultaneously — strong signal. Low evidence may be coincidental.

Alignment stops at the shorter path's length. If paths have different depths, deeper nodes in the longer path simply get no pair — they are not wrong-matched to anything.

---

## The file format

Each line of `category_suspects.jsonl` is a JSON object:

```json
{
  "id": "a3f8b1c2d4e5",
  "company_a": "Woolworths",
  "node_a": "Dairy, Eggs & Fridge",
  "company_b": "Coles",
  "node_b": "Dairy & Fridge",
  "depth_from_leaf": 2,
  "evidence_count": 312,
  "name_similarity": 0.741,
  "example_product_ids": [1042, 2871, 9934],
  "decision": null,
  "note": null
}
```

Fields:
- `id` — stable unique ID for this pair. Use it when calling classify_suspect.
- `company_a` / `node_a` — first company and its category node name at this depth.
- `company_b` / `node_b` — second company and its category node name at this depth.
- `depth_from_leaf` — 0 = leaf (most specific), higher = closer to root (more general).
- `evidence_count` — number of products that produced this pairing.
- `name_similarity` — 0.0–1.0 string similarity of node_a and node_b. 1.0 = identical.
- `example_product_ids` — up to 5 product IDs you can look up if needed for context.
- `decision` — null = undecided (your job). After you classify it, it will be removed from this file.
- `note` — optional explanation of your decision.

---

## Decision criteria

**match** — the two nodes describe the same category concept and should be treated as equivalent.
- Same meaning, even if worded differently. "Dairy, Eggs & Fridge" ↔ "Dairy & Fridge" = match.
- Minor spelling or punctuation variation. "Greek Yoghurt" ↔ "Greek Style Yoghurt" = match.
- One is a subset of the other in name only but they serve the same browse position. "Hair Care" ↔ "Hair" (at depth 1) = likely match if evidence is high.

**not_match** — the two nodes are genuinely different categories that should NOT be merged.
- Clearly different concepts at the same depth. "Bakery" ↔ "Beverages" = not_match.
- One is a promotional/seasonal overlay, the other is a real taxonomy node. "Christmas" ↔ "Snacks & Confectionery" = not_match.
- Different specificity where merging would lose meaning. "Cheese" ↔ "Dairy" = not_match (they are related but Cheese is a sub-category of Dairy, not an equivalent).

**unsure** — you cannot confidently decide without more context.
- The names are ambiguous or too generic. "Food" ↔ "Grocery" at depth 2 may or may not be equivalent depending on the full paths.
- Very low evidence (1–2 products) with dissimilar names — could be coincidental alignment.
- Add a `--note` explaining what would help resolve it.

---

## Tips for deciding quickly

1. **High evidence + high name_similarity (≥ 0.8) → almost always match.** Trust the data.
2. **High evidence + moderate name_similarity (0.5–0.8) → read both names carefully.** Usually match if they're in the same product domain.
3. **Low evidence (< 5) + dissimilar names → lean not_match or unsure.**
4. **depth_from_leaf matters.** At depth 0 (leaf), nodes are very specific — be strict. At depth 2–3 (root), nodes are broad category headers — minor wording differences are fine.
5. **Promotional/seasonal nodes** (Christmas, Down Down, Specials, Limited Time Only, Front Of Store, Big Night In, Weekly Specials) should almost always be not_match against real taxonomy nodes.

---

## How to record your decision

For each entry, call:

```
python manage.py classify_suspect <id> <match|not_match|unsure>
```

With an optional note:

```
python manage.py classify_suspect <id> unsure --note "Too generic at this depth, need full path context"
```

The entry is immediately removed from `category_suspects.jsonl` and archived in `category_decisions.jsonl`. You will never see it again.

Work through the file from top to bottom. Entries are sorted by evidence_count descending — the most-seen pairs first, so high-confidence decisions come early.

---

## Scope

Classify every entry in the file with `"decision": null`. Do not skip any. If you are genuinely unsure after reading both names and the evidence count, use `unsure` with a note — that is a valid decision.

When you finish, all entries will have been moved to the decisions archive and the suspects file will be empty.
