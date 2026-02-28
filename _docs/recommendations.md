# SplitCart Recommendations

A living to-do list of approved improvements. Items are grouped by area and ordered roughly by priority within each group.

---

## Done

- **Fix `PAGE_SIZE`**: Dropped from 500 → 24. Massive performance improvement. (`splitcart/settings.py`)
- **Fix `INTERNAL_IPS`**: Added `127.0.0.1` so Django Debug Toolbar works locally. (`splitcart/settings.py`)
- **Fix sitemap URLs**: Pillar/category pages were listed as `/pillar-pages/{slug}/` in the sitemap but the actual frontend route is `/categories/{slug}/`. Fixed. (`splitcart/sitemaps.py`)

---

## SEO

- [ ] **Add category pages to sitemap** — `/categories/:slug` pages are now in the sitemap (fixed above). Submit the updated sitemap to Google Search Console and request re-indexing.

- [ ] **"How It Works" section on the homepage** — Add a numbered steps component (like futureflower's `ProductCarousel` / steps component) to explain the SplitCart concept. The homepage currently drops users straight into product carousels with no onboarding. New visitors don't understand what to do. The section should explain: (1) search/browse and add items, (2) pick your stores, (3) we split your cart and find the cheapest combination. Needs design thinking before implementation — also consider reducing the number of product carousels on the homepage and making the page more explanatory overall.

- [ ] **Migrate FAQs off dynamic imports** — Currently, pillar page FAQs are loaded via a dynamic TypeScript `import()` keyed by slug. This means Google has to execute an async JS import to see the content. The futureflower pattern passes FAQs directly as a prop from the page component, which is cleaner and consistent. Low priority — the FAQ text is good SEO content but the charts and summary sentences already provide most of the value.

---

## UX — Substitution Flow

- [ ] **Jumpable step indicator** — Currently the only way to go back to a previous substitution item is to click Back repeatedly. Add a clickable step indicator (dots or numbered pills) above the progress bar so users can jump directly to any item they've already seen.

- [ ] **"Review all" list view** — The step-by-step flow is clear for small carts but tedious for large ones. Consider a toggle between the current "one at a time" mode and an "all at once" list view where every item and its substitutes are visible on a single scrollable page. Power users would prefer this.

- [ ] **Running cart summary during substitution** — While working through substitutions the user has no reminder of their full list. A small collapsed header or sidebar showing "12 items in cart · 4 substitutions approved" would provide useful context without taking up space.

---

## UX — Results Page

- [ ] **Explicit "Recommended" label** — The highest-saving tab gets a green badge but users still have to interpret it. Add a clear "Recommended" label to the best-saving tab to remove ambiguity.

- [ ] **Show percentage saving in the panel header** — The savings amount is shown in the tab badge and in the panel as a dollar figure, but the percentage isn't visible inside the panel itself. Showing "You saved 14%" prominently alongside the dollar saving in the panel header would be more satisfying and instantly legible.

---

## Security

*(To be discussed)*

---

## Complexity / Architecture

### Category System

**Issue 1 — Products appearing in wrong primary categories**

Two sub-causes:

**A. Cross-hierarchy contamination via shared category nodes.** Categories are stored uniquely by `(slug, company)`, not by full path. If the same category name appears in two different hierarchy paths (e.g., "Health" under both "Baby & Toddler" and "Health & Beauty"), there is ONE database object with two parents. `PrimaryCategoriesGenerator._get_all_descendants` then traverses the entire subtree of a matched category. When traversal crosses into the wrong parent's branch via a shared node, products from unrelated categories get assigned the wrong primary category (e.g., hair colour products appear on the baby page).

**Proposed fix:** Modify `_get_all_descendants` to stop recursing when it encounters a category whose name has its own explicit entry in the `CATEGORY_MAPPINGS` dict for that company. Parent traversals cover only unmapped gaps; explicitly-mapped categories handle their own subtrees. Small change to the generator.

**B. Incorrect entries in `category_mappings.py`.** Several Woolworths mappings are clearly wrong:
- `'Antipasto': 'Non-Alcoholic Drinks'` → should be `'Miscellaneous'` or `None`
- `'Asian Ready Meals': 'Non-Alcoholic Drinks'` → should be `'International'` or `'Deli'`
- `'Board Games & Puzzles': 'Non-Alcoholic Drinks'` → should be `None`
- `'Chilled Asian': 'Freezer'` → chilled ≠ frozen, should be `'International'` or `'Deli'`

These need a manual audit pass of the full mapping file to catch others like them.

---

## Notes

- Product pages (individual products) are intentionally excluded from the sitemap. With hundreds of thousands of products, indexing them all would waste crawl budget and the pages themselves have thin content (name + price). Not worth pursuing.
- The `PriceComparisonChart` component already renders text summaries ("X% of Fruit tested were cheaper at Woolworths than Coles") in plain HTML — Google can read these. No changes needed there.
