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

## Security

*(To be discussed)*

---

## Complexity / Architecture

*(To be discussed)*

---

## Notes

- Product pages (individual products) are intentionally excluded from the sitemap. With hundreds of thousands of products, indexing them all would waste crawl budget and the pages themselves have thin content (name + price). Not worth pursuing.
- The `PriceComparisonChart` component already renders text summaries ("X% of Fruit tested were cheaper at Woolworths than Coles") in plain HTML — Google can read these. No changes needed there.
