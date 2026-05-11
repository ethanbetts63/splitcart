# SplitCart Next.js SSR Migration Plan

This document began as the investigation and migration plan. It now also records the live Next.js SSR migration work completed on the `splitcart-nextjs-ssr-plan` branch.

## Migration progress log

### 2026-05-10 - Migration started

Branch: `splitcart-nextjs-ssr-plan`

Starting point:

- `_docs/splitcart_nextjs_ssr_migration_plan.md` and `_docs/nextjs_migration.md` were committed by the user in commit `e24db08a` with message `chreckpoint`.
- The working tree showed `_docs/nextjs_migration.md` as deleted before implementation work began. This was not reverted because it was an existing user/worktree change.
- Implementation will follow this document in phases, beginning with a Next.js App Router shell and preserving behavior before deeper SSR conversion.

Progress notes for future agents:

- Keep this section updated after each meaningful migration phase.
- Record build/typecheck failures here when they reveal migration-specific constraints.
- Do not silently change crawler policy. Product pages are still treated as blocked/noindex unless the user explicitly changes that decision.

### 2026-05-10 - Phase 1 parity shell complete

Implemented:

- Installed `next@16.2.6`.
- Changed frontend scripts from Vite to Next:
  - `npm run dev` -> `next dev`
  - `npm run build` -> `next build`
  - added `npm run start`
  - added `npm run typecheck`
- Added `frontend/next.config.ts` with `/api/:path*` rewrites to `DJANGO_API_URL` or `http://localhost:8000`.
- Added `images.disableStaticImages = true` so existing Vite-style image imports remain URL strings. This avoided a broad `.src` rewrite across imported PNG/WebP assets.
- Added `frontend/src/app/` App Router files.
- Added client `AppProviders` and `AppShell` to preserve the old provider/layout behavior.
- Converted active route imports from React Router to Next navigation/link equivalents.
- Renamed `frontend/src/pages/` to `frontend/src/page_components/`. This is required because Next treats `src/pages` as a legacy Pages Router directory and tried to prerender dialog/helper pages.
- Kept the old Vite `src/App.tsx` and `src/main.tsx` out of typechecking through `tsconfig.json` excludes. They are now reference/legacy entry files, not active Next entrypoints.
- Replaced `react-helmet-async` behavior in `components/Seo.tsx` with a structured-data-only bridge. App Router metadata now owns titles, descriptions, canonicals, and noindex rules.
- Added SSR guards to `StoreSearchContext` for `sessionStorage` reads.
- Dynamically imported `StoreMap` with `ssr: false` because Leaflet/react-leaflet touch `window`.
- Moved global CSS imports into `app/layout.tsx`, including `leaflet/dist/leaflet.css` and the category carousel CSS.

Verification:

- `npm run typecheck` passed after the App Router shell changes.
- `npm run build` passed once the `src/pages` directory was renamed, Helmet was removed from active metadata handling, `sessionStorage` was guarded, and Leaflet was made client-only.

Build-specific notes:

- Turbopack could not resolve `@import "tw-animate-css"` through the package style export. The CSS import was changed to `@import "../node_modules/tw-animate-css/dist/tw-animate.css";`.
- Next automatically adjusted `frontend/tsconfig.json` during build by adding `.next/dev/types/**/*.ts` and setting `jsx` to `react-jsx`.

### 2026-05-10 - Phase 2 metadata/crawler controls started

Implemented:

- Added `frontend/src/lib/seo.ts` with shared metadata helpers.
- Added `frontend/src/app/robots.ts`, preserving the existing robots policy:
  - `/product/` remains disallowed.
  - `/search`, `/login`, `/signup`, `/substitutions`, and `/final-cart` remain disallowed.
- Added `frontend/src/app/sitemap.ts`.
- Added `/bargains` to the Next sitemap.
- Added static metadata for `/`, `/contact`, and `/bargains`.
- Added noindex metadata for `/search`, `/product/[slug]`, `/substitutions`, `/final-cart`, `/login`, and `/signup`.
- Added `generateMetadata` for `/categories/[slug]`, fetching `PillarPage` data from Django with 24-hour revalidation.

Still pending:

- Redirects for old `/pillar-pages/:slug/` paths have not yet been added to Next config.
- The visible content for `/`, `/contact`, `/categories/[slug]`, and `/bargains` is still mostly parity-mode client rendering. SSR data passing is the next phase.

Update: old `/pillar-pages/.../` redirects were added to `frontend/next.config.ts` after this note:

- `/pillar-pages/eggs-and-dairy/` -> `/categories/dairy-and-eggs/`
- `/pillar-pages/eggs/` -> `/categories/dairy-and-eggs/`
- `/pillar-pages/pet-and-baby/` -> `/categories/baby/`
- `/pillar-pages/fruit-veg-and-spices/` -> `/categories/fruit-and-veg/`

### 2026-05-10 - Phase 3 initial SSR data pass

Implemented:

- `/` now fetches the default bargain carousel on the server in `app/page.tsx` and passes `initialBargainProducts` into `HomePage`.
- `/bargains` now fetches bargain stats and the first company bargain carousels on the server in `app/bargains/page.tsx`.
- `/categories/[slug]` now fetches the pillar page and initial product carousel data per primary category on the server in `app/categories/[slug]/page.tsx`.
- `ProductCarousel` now supports a server-provided `products` prop while still refetching client-side when the user has a custom store selection (`isUserDefinedList`). This preserves default SSR content without freezing user-specific carousels.

Current SSR scope:

- Homepage static copy and default bargain carousel are present in server-rendered output.
- Bargains page hero/copy/stats/default company carousels are server-data-backed.
- Category pages are server-data-backed for pillar content and initial category carousels.
- `/contact` is still rendered through a client page component, but because it is static/copy-heavy and has no API dependency, the parity shell already prerenders it as static content.

Still intentionally not done:

- Product pages remain noindex/disallowed and were not added to sitemap.
- `/search` remains noindex/disallowed.
- Product detail SSR can be added later for speed, but it should not become indexable without an explicit product SEO decision.
- The old Vite files still exist as excluded reference files (`src/App.tsx`, `src/main.tsx`) and should be removed in a cleanup phase once Next parity is accepted.

Verification:

- `npm run typecheck` passed after SSR prop wiring.
- `npm run build` passed.
- Next build output showed:
  - `/` static with 10 minute revalidation.
  - `/bargains` static with 1 day revalidation.
  - `/categories/[slug]` dynamic server-rendered on demand.
  - `/robots.txt` and `/sitemap.xml` generated by App Router.

Build-specific note:

- Next route segment config requires literal values. `export const revalidate = 60 * 10` was rejected; it was changed to `export const revalidate = 600`. `/bargains` uses `86400`.
- The repo had `frontend/.next` and `frontend/tsconfig.tsbuildinfo` tracked. Running `next build` created a very large generated diff, so these generated artifacts were removed from Git tracking with `git rm -r --cached frontend/.next frontend/tsconfig.tsbuildinfo`, and `frontend/.gitignore` now ignores `.next` and `*.tsbuildinfo`.
- `public/robots.txt` conflicted with `app/robots.ts` and caused `/robots.txt` to return a 500 in dev. The old public file was deleted so App Router owns robots output.
- Next still returned imported static assets as objects at runtime, even with `images.disableStaticImages`. Added `frontend/src/lib/assets.ts` and normalized active image imports with `assetSrc` / `assetSrcSet`. This fixed `[object Object]` in homepage/contact HTML.

Local dev check:

- A Next dev server was started on `http://127.0.0.1:3001` because port 3000 was already serving a different app.
- `http://127.0.0.1:3001/` returned 200.
- `http://127.0.0.1:3001/robots.txt` returned the SplitCart robots policy.
- Homepage and contact HTML were checked for `[object Object]`; none remained in those responses after the asset normalization pass.

### 2026-05-11 - Verification checkpoint

Verification rerun after context compaction:

- `npm run typecheck` passed.
- `npm run build` passed with Next.js `16.2.6`.
- Build output still shows the intended route split:
  - `/` prerendered static with 10 minute revalidation.
  - `/bargains` prerendered static with 1 day revalidation.
  - `/categories/[slug]`, `/product/[slug]`, and `/search` server-rendered on demand.
  - `/robots.txt` and `/sitemap.xml` generated by App Router.

Source-control notes:

- `frontend/.next/**` and `frontend/tsconfig.tsbuildinfo` are staged as deletions from Git tracking. This is intentional generated-artifact cleanup, not an app deletion. The files can continue to exist locally after builds because `frontend/.gitignore` now ignores them.
- `frontend/src/pages/**` was replaced by `frontend/src/page_components/**` so Next does not treat old route component files as Pages Router entries. Stage this as a rename/add-delete set when committing.
- Do not restore `frontend/public/robots.txt`; App Router now owns robots output through `frontend/src/app/robots.ts`.

### 2026-05-11 - Visual parity bugfixes

Issue found during browser testing:

- The app looked like mostly raw HTML in Next dev because Tailwind was only configured through the old Vite plugin (`@tailwindcss/vite`). Next does not run `vite.config.ts`, so Tailwind utilities were not being compiled through the Next CSS pipeline.
- `StoreListContext` crashed on startup when `/api/store-lists/active/` returned no JSON body or an otherwise empty response. The provider assumed `activeData.store_list` always existed.

Fixes:

- Installed `@tailwindcss/postcss` and added `frontend/postcss.config.mjs` so Next compiles Tailwind v4 styles.
- Made the active store-list read null-safe with `activeData?.store_list ?? null`, preserving the existing "new user/no active list" branch.

Verification:

- `npm run typecheck` passed.
- `npm run build` passed.
- Production build emitted a large CSS chunk again (`.next/static/chunks/0-qmiqfx.42b_.css`, about 100 KB), which confirms Tailwind utilities are being generated.

Dev note:

- Because `postcss.config.mjs` is a new build config file, an already-running `next dev` process may need to be restarted before the styling fix appears in the browser.

The goal is to apply the useful parts of the AllBikes Vite -> Next.js migration to SplitCart, with a narrower focus: frontend indexable pages and the SEO/performance benefit of rendering meaningful HTML on the server.

## Executive summary

SplitCart is currently a Vite React single-page app served by Django. Public routes are defined in `frontend/src/App.tsx`, rendered through React Router, and SEO tags are added at runtime through `react-helmet-async`.

This means crawlers initially receive the same shell HTML from `frontend/index.html` for almost every route:

- Static metadata is only `title=SplitCart` plus global tags.
- Page-specific title, description, canonical tags, structured data, product names, category content, and product grids are added after client JavaScript runs.
- SEO-critical data is mostly fetched in client components through `useApiQuery`, `ProductCarousel`, and `GridSourcer`.

The AllBikes lesson applies directly: moving route metadata into Next.js is necessary, but the real performance/indexing gain comes from making high-value public pages render their visible content on the server.

Recommended approach:

1. Create a Next.js App Router frontend in `frontend/`.
2. Keep Django as the API/database application.
3. Use server route files as data loaders for indexable pages.
4. Pass initial server data into existing client components first.
5. Split into cleaner server/client components only after parity is working.

## Current frontend architecture

Current frontend stack:

- Vite app in `frontend/`
- React 19
- React Router 7
- React Query 5
- Tailwind 4 / shadcn-style UI components
- `react-helmet-async` for SEO
- Django serves the built app through `ReactAppView`
- Vite dev proxy sends `/api` to Django

Current route tree in `frontend/src/App.tsx`:

| Route | Current component | Current index intent |
| --- | --- | --- |
| `/` | `HomePage` | Indexable |
| `/contact` | `ContactPage` | Indexable |
| `/categories/:slug` | `PillarPage` | Indexable |
| `/bargains` | `BargainsPage` | Intended indexable, but missing from sitemap |
| `/search` | `SearchResultsPage` | Noindex/disallowed |
| `/product/:slug` | `ProductPage` | SEO component exists, but `/product/` is disallowed in robots |
| `/substitutions` | `SubstitutionPage` | Disallowed |
| `/final-cart` | `FinalCartPage` | Disallowed |
| `/login` | `LoginPage` | Disallowed/noindex |
| `/signup` | `SignupPage` | Disallowed |

Current sitemap in `splitcart/sitemaps.py` includes:

- `/`
- `/contact`
- 11 category pillar routes under `/categories/.../`

Current `frontend/public/robots.txt` disallows:

- `/admin/`
- `/api/`
- `/substitutions/`
- `/final-cart/`
- `/search`
- `/login`
- `/signup`
- `/product/`

Important implication: product pages currently behave like SEO pages in code, but robots block crawling. The migration should not accidentally make product pages indexable without an explicit decision.

## Current SEO/data problems

### Runtime-only metadata

`frontend/src/components/Seo.tsx` uses Helmet. In a Vite SPA, this updates the browser after hydration rather than producing route-specific metadata in the initial HTML.

Affected pages:

- `/`
- `/contact`
- `/bargains`
- `/product/:slug`
- `/search` noindex

`PillarPage` currently does not render a `Seo` component even though category pillar pages are in the sitemap and are high-priority SEO pages.

### Client-only page data

The pages with the biggest SSR upside are currently loading meaningful content in the browser:

- `PillarPage` fetches `/api/pillar-pages/:slug/` through `useApiQuery`.
- `PillarPage` product carousels fetch `/api/products/?primary_category_slugs=...`.
- `BargainsPage` fetches `/api/stats/bargains/` through `useApiQuery`.
- `BargainsPage` company bargain carousels fetch `/api/products/bargain-carousel/`.
- `ProductPage` fetches `/api/products/:id/`.
- `ProductPage` substitutes fetch `/api/products/:id/substitutes/`.
- `SearchResultsPage` fetches product grids through `GridSourcer`.
- `CategoryBar` fetches `/api/categories/primary/`.
- `HomePage` bargain carousel fetches `/api/products/bargain-carousel/`.

Static copy-heavy pages like `/` and `/contact` have meaningful visible content in component markup, but in the current SPA it is still not present in the server response because Django serves the same app shell.

### Indexing policy drift

There is disagreement between the app and crawler controls:

- `/bargains` has SEO metadata and strong content, but it is absent from the sitemap.
- `/product/:slug` has SEO metadata and Product JSON-LD, but `/product/` is disallowed in robots.
- `/search` is noindex/disallowed, but category bar links point to `/search?primary_category_slug=...` for category grids.

Before deployment, decide whether products and category-result grids should remain utility pages or become SEO landing pages.

## Recommended target architecture

Target structure, following the AllBikes migration pattern:

```text
splitcart/
  splitcart/             Django project
  frontend/              Next.js App Router frontend
  _docs/
```

Next.js should become the public web server for the frontend. Django should remain the API server.

Local development:

- Django: `python manage.py runserver` on port 8000
- Next.js: `cd frontend && npm run dev` on port 3000
- Next.js rewrites `/api/:path*` to Django

Production:

- Deploy frontend to Vercel or another Node-capable host.
- Keep Django/PythonAnywhere for API and data management unless there is a separate infrastructure decision.
- Set `DJANGO_API_URL` in the Next.js environment.
- Update Django `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` for the frontend domain.

Use an App Router layout like:

```text
frontend/app/
  layout.tsx
  page.tsx
  contact/page.tsx
  bargains/page.tsx
  categories/[slug]/page.tsx
  search/page.tsx
  product/[slug]/page.tsx
  login/page.tsx
  signup/page.tsx
  substitutions/page.tsx
  final-cart/page.tsx
  sitemap.ts
  robots.ts
frontend/page_components/
frontend/components/
frontend/lib/
```

As with AllBikes, initially move current route components into `page_components/` and let `app/*/page.tsx` wrappers load data and metadata.

## API proxy setup

Add `frontend/next.config.ts`:

```ts
const nextConfig = {
  async rewrites() {
    const apiUrl = process.env.DJANGO_API_URL ?? "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${apiUrl}/api/:path*` }];
  },
};

export default nextConfig;
```

Unlike AllBikes, there is no known trailing-slash redirect loop yet. Still test API calls with Django `APPEND_SLASH` behavior before deployment. If Next and Django fight over slash normalization, bring over the AllBikes `skipTrailingSlashRedirect: true` setting.

## Metadata strategy

Replace `react-helmet-async` with Next.js route metadata.

Create `frontend/lib/seo.ts` with:

- canonical URL helper
- shared site name
- default Open Graph image
- helpers for `Metadata`
- helpers for `robots: { index: false, follow: false }`

Route metadata targets:

| Route | Metadata source |
| --- | --- |
| `/` | static metadata from current `HomePage` |
| `/contact` | static metadata from current `ContactPage` |
| `/bargains` | static metadata from current `BargainsPage` |
| `/categories/[slug]` | `generateMetadata` from `/api/pillar-pages/:slug/` |
| `/product/[slug]` | keep noindex unless robots policy changes; if indexed, `generateMetadata` from `/api/products/:id/` |
| `/search` | noindex |
| `/substitutions` | noindex |
| `/final-cart` | noindex |
| `/login` | noindex |
| `/signup` | noindex |

Structured data should move out of Helmet. Use small server components or inline script components rendered by the route:

- WebSite JSON-LD on `/`
- ContactPage JSON-LD on `/contact`
- WebPage JSON-LD on `/bargains`
- FAQPage JSON-LD on FAQ-heavy pages if desired
- Product JSON-LD only if `/product/` is intentionally made indexable
- ItemList JSON-LD for server-rendered product carousels/grids

## SSR migration priorities

### Phase 1: Next shell with route parity

Goal: get the current app running under the App Router without changing behavior.

Tasks:

- Install Next.js and update scripts.
- Replace Vite entrypoint with Next App Router.
- Move current pages to `frontend/page_components/`.
- Create `app/*/page.tsx` route wrappers.
- Move global providers into a client `Providers` component.
- Convert React Router imports to `next/navigation` and `next/link`.
- Replace `BrowserRouter`, `Routes`, `Outlet`, and `useLocation` with App Router equivalents.
- Preserve the current layout: nav, category bar, footer, settings dialog, toaster, next button.
- Keep all data fetching client-side for this phase.

Expected friction:

- `react-router-dom` links and hooks are widespread.
- `import.meta.env` must become `process.env.NEXT_PUBLIC_*`.
- Browser APIs in providers/components need `"use client"` boundaries.
- Static image imports may need `.src` if kept in plain `<img>` elements.

Acceptance:

- Every current route renders.
- `npm run build` passes.
- No behavior changes beyond framework routing.

### Phase 2: Next metadata, sitemap, and robots

Goal: make crawler controls server-rendered and explicit.

Tasks:

- Remove route-level dependency on `react-helmet-async`.
- Add metadata for all routes listed above.
- Add `app/sitemap.ts`.
- Add `app/robots.ts`.
- Mirror current robots policy first. Do not unblock `/product/` during the framework migration.
- Add `/bargains` to the sitemap unless there is a reason to keep it out.
- Add category routes from the same list currently in `splitcart/sitemaps.py`, or fetch from the API if stable enough.
- Add redirects for old pillar slugs currently handled by Django:
  - `/pillar-pages/eggs-and-dairy/` -> `/categories/dairy-and-eggs/`
  - `/pillar-pages/eggs/` -> `/categories/dairy-and-eggs/`
  - `/pillar-pages/pet-and-baby/` -> `/categories/baby/`
  - `/pillar-pages/fruit-veg-and-spices/` -> `/categories/fruit-and-veg/`

Acceptance:

- Initial HTML contains correct title/description/canonical for indexable pages.
- `robots.txt` and `sitemap.xml` are served by Next.
- Current noindex/disallow policy is preserved unless deliberately changed.

### Phase 3: SSR currently indexable pages

Goal: make the current sitemap/indexable pages render meaningful content without client JavaScript.

#### `/`

Priority: high.

Current visible content is mostly static, but the server response is still a SPA shell. Convert the route to a server component and pass initial data to client widgets.

Server-render:

- hero copy and image
- browse category tiles
- how-it-works section
- FAQ copy
- initial bargain carousel products from `/api/products/bargain-carousel/?limit=20`

Keep client-only:

- selected-store customization after hydration
- cart/next-button behavior
- settings dialog
- carousel scroll/resize behavior

Recommended revalidation: 10-30 minutes for the homepage bargain carousel.

#### `/contact`

Priority: high, simple.

Server-render:

- page metadata
- hero copy
- contact details
- other sites section

Keep client-only only if a child component truly needs browser APIs. This page should probably become almost entirely server-rendered.

Recommended revalidation: static.

#### `/categories/[slug]`

Priority: highest SEO payoff.

Server-render:

- `pillarPage` from `/api/pillar-pages/:slug/`
- hero title/introduction
- primary category sections
- price comparison charts where possible
- FAQ copy
- initial carousel products per primary category

Keep client-only:

- carousel interaction
- selected-store-specific replacement after hydration
- "select a location" dialog

Current backend support is good:

- `/api/pillar-pages/:slug/` is cached for 24 hours.
- `/api/products/?primary_category_slugs=...&ordering=carousel_default&limit=20` already supports carousel data.
- Primary category data includes `price_comparison_data`.

Recommended route behavior:

- Use `generateStaticParams` for the 11 known category slugs, or use dynamic rendering with revalidation.
- Use `notFound()` for missing pillar pages.
- Revalidate every 24 hours for pillar copy.
- Revalidate product carousel sections every 10-60 minutes depending on price freshness requirements.

Important design choice:

- Current `PillarPage` has no SEO metadata. Add route-specific title/description from the API, or extend the `PillarPage` model/serializer with explicit SEO fields if the generated copy is not strong enough.

### Phase 4: SSR `/bargains`

Goal: make the bargains landing page a fully indexable page.

Server-render:

- title/description/canonical
- hero copy
- company bargain carousel initial products for Coles, Woolworths, Aldi, and IGA
- bargain stats from `/api/stats/bargains/`
- FAQ copy

Keep client-only:

- selected-store-specific updates
- carousel interaction
- chart animation/responsiveness if required

Backend support:

- `/api/stats/bargains/` is cached for 24 hours.
- `/api/products/bargain-carousel/?company_name=...&limit=20` is cached for 24 hours.

Recommended revalidation: 24 hours, unless bargain data is refreshed more frequently.

Sitemap:

- Add `/bargains` to the sitemap in this phase if not done in Phase 2.

### Phase 5: Decide product-page indexing

Current policy blocks `/product/` in robots. Do not SSR product pages for indexing until the product indexing decision is explicit.

Reasons to keep product pages blocked for now:

- There may be a very large number of product URLs.
- Prices and availability are volatile.
- Product slugs include IDs, but old slug variants may duplicate the same product.
- Some products may have thin content beyond price comparison.
- Store-specific pricing can change page content based on user-selected stores.

If product pages remain blocked:

- Keep `/product/[slug]` as a client-heavy or partially SSR utility route.
- Add noindex route metadata.
- Preserve robots disallow.
- You may still server-render the product detail for speed, but do not include it in sitemap.

If product pages become indexable later:

- Remove `/product/` from robots.
- Add product sitemap generation with limits and freshness rules.
- Canonicalize by current slug from the API, not by arbitrary route slug.
- Redirect stale slug text to `/product/{current-slug}` when the ID is valid.
- Server-render product name, brand, size, image, price comparison, and JSON-LD.
- Revalidate every 30 minutes or use cache tags after scrape/update jobs.
- Consider only indexing products with enough price coverage, image availability, and category assignment.

### Phase 6: Search and category result grids

Current `/search` is noindex and disallowed. Keep it that way during the initial migration.

Reason:

- Search URLs can create an unlimited crawl space.
- Query-string pages are harder to canonicalize.
- User-selected stores materially change results.

Potential future SEO improvement:

- Create clean, indexable category listing routes instead of indexing `/search`.
- Example: `/categories/[slug]/products` or `/products/category/[slug]`.
- Server-render page 1 from `/api/products/?primary_category_slug=...&page=1&page_size=20`.
- Keep sort/page/filter interactions client-side.
- Canonicalize page 1 and decide whether paginated pages should be indexable.

Do not index arbitrary text search URLs.

## Component conversion notes

### Providers and layout

These must remain client-side:

- `AuthProvider`
- `CartProvider`
- `StoreListProvider`
- `StoreSearchProvider`
- `DialogProvider`
- `SettingsDialog`
- `Toaster`

Create a client `Providers.tsx` and use it inside `app/layout.tsx`.

### Layout route awareness

Current `Layout` uses `useLocation()` to decide:

- whether to show `CategoryBar`
- whether to show `NextButton`

In Next.js, move this logic to a client layout component using `usePathname()`.

### CategoryBar

`CategoryBar` currently fetches categories client-side. For better perceived performance:

- Server-fetch primary categories in the root layout or route group.
- Pass them into a client `CategoryBar`.
- Keep animation and random navigation client-side.

### ProductCarousel

Current component already accepts `products: initialProducts`. This is a good migration seam.

Plan:

- Server pages fetch carousel products.
- Pass them as `products`.
- Keep the existing browser fallback fetch only when `initialProducts` is absent.
- After hydration, optionally refetch if the user has selected custom stores.

### GridSourcer

Current `GridSourcer` does not accept initial data. If search/category grids are SSR'd later, add:

- `initialResponse?: PaginatedProductResponse`
- `initialPage?: number`
- `initialParamsKey?: string`

Then React Query can use `initialData` or skip initial loading.

### ProductPage

Current product route extracts the ID from the final slug segment. Keep that behavior initially.

Need guardrails if indexed:

- Validate the product ID.
- Fetch product on the server.
- Compare requested slug with `product.slug`.
- Redirect if mismatched.
- Handle missing products with `notFound()`.

### Images

Current plain `<img>` usage is acceptable for parity, but Next migration has two likely issues:

- Imported PNG/WebP values become `StaticImageData`; plain `<img src={importedImage}>` may need `.src`.
- Remote product images from supermarkets require `images.remotePatterns` if migrating to `next/image`.

Initial recommendation:

- Keep plain `<img>` for parity.
- Fix imported image `.src` issues as they appear.
- Move to `next/image` only after SSR parity.

## Backend/API changes worth considering

No backend changes are strictly required for the first SSR pass, but these would make the migration cleaner:

1. Add SEO fields to `PillarPage`
   - `seo_title`
   - `seo_description`
   - optional `og_image`

2. Add a product lookup endpoint by slug
   - Current frontend extracts ID from slug and calls `/api/products/:id/`.
   - This is workable, but `/api/products/by-slug/:slug/` would simplify canonical validation.

3. Add a sitemap-friendly product eligibility endpoint if products become indexable
   - Only return products with image, prices, category, and enough store/company coverage.

4. Expose primary categories as static-ish data for layout SSR
   - Existing `/api/categories/primary/` is cached and likely enough.

5. Consider cache invalidation hooks after scraping/import jobs
   - Current API cache durations are useful, but Next revalidation should align with scrape cadence.

## Routes that should remain client-only or noindex

Do not spend SSR effort on these beyond route parity:

- `/login`
- `/signup`
- `/substitutions`
- `/final-cart`
- cart dialog pages
- edit location dialog
- checkout-like cart optimization flows
- authenticated or anonymous-session-specific cart/store-list views

These routes depend on auth, anonymous IDs, local state, or user-selected stores. Server rendering them is unlikely to help SEO and may add complexity.

## Suggested implementation order

1. Framework migration only
   - Add Next.js App Router.
   - Port routes/components.
   - Keep client fetching.

2. Metadata and crawler controls
   - Replace Helmet.
   - Add `sitemap.ts` and `robots.ts`.
   - Preserve robots policy.
   - Add `/bargains` to sitemap.

3. Static/public SSR
   - `/`
   - `/contact`

4. Data-backed SEO SSR
   - `/categories/[slug]`
   - `/bargains`

5. Optional utility SSR
   - `/product/[slug]` as noindex for speed only

6. Product indexing decision
   - Only after explicit product SEO policy is agreed.

7. Optional category product listing routes
   - Create clean indexable listing URLs instead of indexing `/search`.

## Acceptance criteria

For every indexable route migrated to SSR:

- Initial HTML contains the route's real title, meta description, canonical, and visible page content.
- Initial HTML contains meaningful H1/body copy without waiting for client JavaScript.
- API failures produce a useful fallback or `notFound()`, not a blank loading screen.
- Existing cart, selected-store, dialog, carousel, and navigation behavior still works after hydration.
- The current robots/noindex policy is preserved unless deliberately changed.
- `npm run build` passes.
- TypeScript passes.
- Lighthouse/Google inspection should show meaningful rendered HTML for `/`, `/contact`, `/bargains`, and representative `/categories/:slug` pages.

## Open decisions

Before starting the actual migration, decide:

1. Should `/product/` remain blocked, or should selected products become indexable?
2. Should `/bargains` be added to the sitemap? Recommendation: yes.
3. Should category product grids get clean SEO routes, or remain noindex under `/search`?
4. Where will the Next.js frontend be deployed: Vercel, same host, or another Node-capable host?
5. What is the correct revalidation cadence after price scrapes and bargain summary generation?

## Investigation file map

Key files reviewed:

- `frontend/src/App.tsx` - current React Router routes and layout
- `frontend/src/main.tsx` - Vite/BrowserRouter/providers entrypoint
- `frontend/src/components/Seo.tsx` - runtime Helmet SEO
- `frontend/src/pages/HomePage.tsx`
- `frontend/src/pages/ContactPage.tsx`
- `frontend/src/pages/PillarPage.tsx`
- `frontend/src/pages/BargainsPage.tsx`
- `frontend/src/pages/ProductPage.tsx`
- `frontend/src/pages/SearchResultsPage.tsx`
- `frontend/src/components/ProductCarousel.tsx`
- `frontend/src/components/GridSourcer.tsx`
- `frontend/src/components/CategoryBar.tsx`
- `frontend/public/robots.txt`
- `splitcart/urls.py`
- `splitcart/sitemaps.py`
- `data_management/views/react_app_view.py`
- `data_management/views/pillar_page_view.py`
- `products/views/product_list_view.py`
- `products/views/product_detail_view.py`
- `products/views/bargain_carousel_view.py`
- `products/views/bargain_stats_view.py`
- `products/serializers/product_serializer.py`
