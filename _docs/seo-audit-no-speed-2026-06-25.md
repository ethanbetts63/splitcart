# SplitCart SEO Audit, Excluding Speed

Date: 2026-06-25
Site: https://www.splitcart.com.au/
Scope: full-site SEO audit excluding speed, Core Web Vitals, resource weight, and loading performance.

## Evidence Used

- `search_console.txt` excerpt supplied by Ethan.
- Live crawl of `https://www.splitcart.com.au/`, `robots.txt`, `sitemap.xml`, sitemap URLs, selected product/search/privacy URLs, HTTP and HTTPS variants.
- Local implementation review in `frontend/src/app`, `frontend/src/components`, and `frontend/src/lib/seo.ts`.

No cached SEO context existed in `.seo-cache/`; this audit used fresh evidence.

## Executive Summary

Non-speed SEO health score: **68/100**.

SplitCart has a clear product idea and a solid initial indexable surface: homepage, `/bargains`, category pillar pages, metadata, sitemap, robots.txt, and some structured data are all in place. The biggest issue is not technical crawl failure; it is that Google currently has too little high-intent, indexable content to rank. The current Search Console excerpt shows impressions for terms like `compare supermarket prices`, `grocery price comparison`, `food shopping price comparison`, `cheapest vegetables australia`, and `aldi fruit prices`, but the site only exposes 14 sitemap URLs and most category pages are broad.

The biggest SEO opportunities are:

1. Build indexable pages that directly match existing query demand.
2. Decide what product pages are meant to do for SEO, then fix the current robots/noindex conflict.
3. Expand thin category pages and add comparison-led content blocks.
4. Add stronger structured data for Organization/WebApplication/BreadcrumbList and category ItemLists.
5. Fix the apex domain certificate/redirect problem so `https://splitcart.com.au/` does not fail.
6. Add `llms.txt` and more citation-ready factual sections for AI search surfaces.

Speed was intentionally not audited.

## Search Console Read

Search Console is showing almost no clicks. The two clicked pages in the excerpt are:

- `/categories/drinks`: 1 click, 46 impressions, 2.2% CTR, avg position 14.6.
- `/categories/dairy-and-eggs`: 1 click, 34 impressions, 2.9% CTR, avg position 11.7.

The homepage has 206 impressions and 0 clicks at avg position 28.4. `/categories/fruit-and-veg` has 127 impressions and 0 clicks at avg position 23.0.

Query intent is clear:

- Core category: `grocery price comparison`, `grocery shopping price comparison`, `compare supermarket prices`.
- Australia modifier: `price compare australia`, `price comparison aus`.
- Fresh produce: `cheapest vegetables australia`, `cheapest fruits in australia`, `aldi fruit prices`, `aldi vegetables prices`.
- Store/product long tail: `scorched peanut bar coles`.

Recommendation: treat this as a demand map. Do not start by writing random blog posts; build landing pages around these query families.

## Critical Issues

### 1. Apex Domain Is Broken

`https://splitcart.com.au/` failed with an expired certificate error. `http://splitcart.com.au/` redirected to `http://global_errors.all.com/`, not to the canonical `https://www.splitcart.com.au/`.

Impact: branded links, citations, browser autocomplete, and unqualified links to the apex domain can fail or leak authority.

Fix:

- Configure the apex domain in Vercel/DNS.
- Renew or attach the correct certificate.
- 301 redirect all variants to `https://www.splitcart.com.au/`.
- Test:
  - `http://splitcart.com.au/`
  - `https://splitcart.com.au/`
  - `http://www.splitcart.com.au/`
  - `https://www.splitcart.com.au/`

### 2. Product URL Strategy Is Conflicted

Product pages are linked from indexable pages like `/bargains`, but `robots.txt` disallows `/product/`, and the product route emits `noindex,nofollow`.

Current implementation:

- `frontend/src/app/robots.ts` disallows `/product/`.
- `frontend/src/app/product/[slug]/page.tsx` exports `noindexMetadata`.
- `/bargains` links to product URLs.
- Product pages have useful Product schema and real price comparison content, but Google is told not to use it.

Why this matters: if Google discovers product URLs from links but cannot crawl them because of robots.txt, it may be unable to see the `noindex`. That creates messy URL discovery and wastes internal link equity. More importantly, product queries are likely one of SplitCart's strongest long-tail opportunities.

Choose one of these strategies:

- **Recommended:** make selected product pages indexable once quality gates are met. Add unique title/description/canonical per product, keep Product schema, include price freshness wording, and add them to a product sitemap in controlled batches.
- **Alternative:** if product pages must stay non-indexable, remove the robots disallow and keep `noindex,follow` so Google can see the directive and follow links, or stop linking product pages from indexable pages.

Do not combine robots disallow with noindex for URLs that are internally linked.

## High Priority Issues

### 3. Sitemap Is Too Small For The Search Opportunity

The sitemap lists 14 URLs:

- Homepage
- Contact
- Bargains
- 11 category pages

This is clean, but too shallow. For a grocery comparison site, the organic surface should include category, subcategory, comparison, deal, and selected product or product-family pages.

Recommended additions:

- `/compare-supermarket-prices/`
- `/grocery-price-comparison/`
- `/cheapest-supermarket-australia/`
- `/cheapest-fruit-australia/`
- `/cheapest-vegetables-australia/`
- `/aldi-fruit-and-veg-prices/`
- `/coles-vs-woolworths-prices/`
- `/aldi-vs-coles-vs-woolworths/`
- `/categories/fruit/`
- `/categories/vegetables/`
- `/categories/milk/`
- `/categories/eggs/`
- `/categories/chocolate/`

Build these as useful landing pages, not thin doorway pages. Each page needs original explanation, live or semi-live comparison data, examples, FAQs, internal links, and a clear way to use SplitCart.

### 4. Some Category Pages Are Thin

Crawler word counts:

- `/categories/baby/`: 161 words.
- `/categories/international-herbs-and-spices/`: 265 words.
- `/categories/health-beauty-and-supplements/`: 301 words.
- `/categories/drinks/`: 361 words.
- Stronger pages include `/bargains` at 1715 words, `/categories/dairy-and-eggs/` at 1166 words, and `/categories/snacks-and-sweets/` at 1200 words.

Thin pages can still rank if the product/data experience is uniquely valuable, but the current pages need more static, crawlable explanation and evidence.

For each category page, add:

- A "Which supermarket is cheapest for [category]?" section.
- A "What we compare" section naming subcategories and examples.
- A "How prices differ by store" section using current aggregated data.
- Links to subcategory pages or filtered comparison pages.
- 4-6 FAQs where there is genuine search demand.

### 5. Homepage Is Ranking For The Right Ideas But Not Winning Clicks

Homepage Search Console signal: 206 impressions, 0 clicks, avg position 28.4.

The homepage title is `SplitCart: Australian Grocery Price Comparison`, which is decent. However, the H1 is `The Cheapest Way to Buy Groceries`, while visible copy and category links do most of the semantic work.

Improve by making the above-the-fold language closer to search demand:

- Title option: `SplitCart: Compare Supermarket Prices in Australia`
- H1 option: `Compare Grocery Prices Across Coles, Woolworths, Aldi and IGA`
- Supporting copy should still explain the cart-splitting differentiator.

This better matches `compare supermarket prices`, `grocery price comparison`, and `price comparison australia`.

### 6. Structured Data Is Partial

Current positives:

- Homepage has `WebSite` and `SearchAction`.
- `/bargains` has `WebPage` and FAQ schema.
- Product pages have Product schema with AggregateOffer.
- Contact page has `ContactPage`, `ContactPoint`, and `WebPage`.

Gaps:

- No Organization or WebApplication schema.
- No BreadcrumbList schema on category/product pages.
- Category pages generally lack WebPage/CollectionPage schema.
- Client-rendered ItemList schema from `JsonLdItemList` may not reliably appear in raw server HTML for all crawlers.
- FAQPage is present on commercial pages. This is not a Google rich-result growth lever for most commercial sites anymore, though it can still help LLM/citation interpretation.

Recommended schema:

- Add sitewide `Organization` or `SoftwareApplication/WebApplication`.
- Add `BreadcrumbList` on categories, bargains, and product pages.
- Add `CollectionPage` or `ItemList` on category pages with top products or subcategories.
- Keep Product schema only on pages that are crawlable and indexable.

## Medium Priority Issues

### 7. Category URL Canonical/Sitemap Format Is Inconsistent

Sitemap category URLs use trailing slash, for example `/categories/drinks/`, while canonicals point to no trailing slash, for example `https://www.splitcart.com.au/categories/drinks`.

Both URL forms return 200, and the canonical points to the no-slash version. This is not catastrophic, but it is unnecessary ambiguity.

Fix:

- Make sitemap URLs match canonicals exactly.
- Prefer one version and redirect the other where practical.

### 8. Search Pages Are Noindexed But Heavily Linked As Exploration Targets

Category pages link to `/search?primary_category_slug=...`; `/bargains` links to `/search?bargain_company=...`. The `/search` route is `noindex,nofollow`.

That is reasonable for arbitrary search results, but if a filter has search demand and stable content, promote it to an indexable landing page rather than leaving it as a noindexed search parameter.

Examples:

- `/categories/fruit/` instead of `/search?primary_category_slug=fruit`
- `/stores/coles/bargains/` instead of `/search?bargain_company=Coles`
- `/stores/woolworths/bargains/`

### 9. Internal Linking Is Too App-Like

The site links heavily through product cards and search-result style flows. It needs more editorial/contextual internal links:

- Homepage should link to the highest-demand comparison pages.
- Category pages should link to related categories and store comparison pages.
- Bargains page should link to store-specific and category-specific bargains.
- Product pages, if indexed, should link back to category, brand, store, and similar products.

### 10. AI Search Readiness Is Underdeveloped

`https://www.splitcart.com.au/llms.txt` returns 404.

The site has some useful founder copy and FAQs, but AI-search citation surfaces prefer clear, extractable factual passages. Add sections that can be quoted or summarized easily:

- What SplitCart compares.
- Stores covered.
- How often prices update.
- How substitutions work.
- What "cheapest" means.
- Data limitations by IGA/local store.
- Contact/about details.

Add `/llms.txt` with canonical pages and short descriptions.

### 11. Image Alt Coverage Is Mostly Good Except Homepage

Crawl result:

- Homepage: 17 images, 12 missing alt.
- Most category pages: 2 images, 0 missing alt.
- `/bargains`: 42 images, 0 missing alt.

Fix missing homepage alt text for decorative/category icon images. If an image is decorative, use empty `alt=""`; if it communicates a category, use a descriptive alt.

## Low Priority Issues

### 12. Security Headers Could Be Stronger

Observed:

- HSTS is present.

Not observed in sampled headers:

- Content-Security-Policy
- X-Frame-Options or frame-ancestors equivalent
- X-Content-Type-Options
- Referrer-Policy

This is not a ranking lever in the normal sense, but it supports trust and reduces risk.

### 13. Contact Page Has Unrelated Outbound Project Promotion

The contact page includes other projects. That is fine personally, but it dilutes topical relevance for a grocery comparison brand. If the goal is SEO focus, move those links lower, nofollow them, or keep them on a founder/about page instead.

## Suggested Content Roadmap

Phase 1: Query-match pages from existing GSC signals.

1. `Compare Supermarket Prices in Australia`
2. `Grocery Price Comparison Australia`
3. `Cheapest Fruit in Australia`
4. `Cheapest Vegetables in Australia`
5. `Aldi Fruit and Vegetable Prices`
6. `Coles vs Woolworths vs Aldi Price Comparison`

Phase 2: Category/subcategory expansion.

1. Fruit
2. Vegetables
3. Milk
4. Eggs
5. Cheese
6. Chocolate
7. Soft drinks
8. Cleaning products

Phase 3: Controlled product SEO.

Index only products with:

- Stable slug.
- Product name, brand, size, image.
- At least 2 store prices.
- Product schema.
- Category/breadcrumb links.
- Price freshness copy.
- Enough related products to avoid dead-end pages.

## Prioritized Action Plan

### Critical

1. Fix apex domain certificate and redirect all apex/non-www/http variants to `https://www.splitcart.com.au/`.
2. Resolve `/product/` robots/noindex conflict. Prefer indexing selected high-quality product pages, or allow crawl with `noindex,follow`.

### High

1. Build 5-8 demand-matched landing pages from the Search Console query families.
2. Expand thin category pages, especially Baby, International/Herbs/Spices, Health/Beauty/Supplements, and Drinks.
3. Align homepage title/H1/copy with "compare supermarket prices in Australia".
4. Add Organization/WebApplication, BreadcrumbList, and CollectionPage/ItemList schema.

### Medium

1. Make sitemap URLs match canonical URL format.
2. Promote valuable search-filter pages into clean indexable routes.
3. Add contextual internal links from homepage, bargains, and category pages.
4. Add `/llms.txt` and clearer citation-ready factual sections.
5. Fix homepage image alt handling.

### Low

1. Add stronger security headers.
2. Reduce unrelated project promotion on the contact page.

## Implementation Notes From Code Review

- Robots exclusions live in `frontend/src/app/robots.ts`.
- Sitemap paths live in `frontend/src/app/sitemap.ts`.
- Shared metadata helper lives in `frontend/src/lib/seo.ts`.
- Category metadata and canonical paths are generated in `frontend/src/app/categories/[slug]/page.tsx`.
- FAQ schema is emitted by `frontend/src/components/FaqSection.tsx`.
- Product carousel links and client-side ItemList schema are in `frontend/src/components/ProductCarousel.tsx`.
- Product pages emit Product schema in `frontend/src/page_components/ProductPage.tsx`, but route metadata currently noindexes them.

## Sources

- Homepage: https://www.splitcart.com.au/
- Robots: https://www.splitcart.com.au/robots.txt
- Sitemap: https://www.splitcart.com.au/sitemap.xml
- Search Console excerpt: `C:\Users\ethan\coding\splitcart\search_console.txt`
