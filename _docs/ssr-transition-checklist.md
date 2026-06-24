# SSR Transition Checklist

Phases 1–3 of the original migration plan are complete (Next.js shell, metadata/sitemap/robots,
initial server-side data passing). This document picks up from that point and tracks the
remaining component-level conversion work. Check items off as they are done.

See `splitcart_nextjs_ssr_migration_plan.md` for the full history of what was done and why.

---

## Current state

The app already runs on Next.js App Router. For indexable pages the server route files
(`src/app/*/page.tsx`) fetch data and pass it as props into the page_components. Those
page_components are all still `"use client"`, but Next.js SSR renders client components to
HTML anyway, so the initial payload does reach crawlers. The remaining problem:

- The page_components themselves are larger JS bundles than necessary.
- Static sections (hero copy, FAQs, comparison charts) are hydrated as client components when
  they have no need to be.
- `useStoreList()` is called at the top of every indexable page just to pass `storeIds` into
  `ProductCarousel` — the page shouldn't need to know about store context at all.
- Dead Vite files still exist and inflate the apparent complexity of the repo.

---

## The critical enabler — do this first

**Make `ProductCarousel` self-contained.**

Currently every indexable page calls `useStoreList()` and passes `storeIds`, `isUserDefinedList`,
and `isDefaultStores` as props to `ProductCarousel`. If `ProductCarousel` reads `useStoreList()`
internally, the pages no longer need to be client components just to supply those values.

- [x] Add `useStoreList()` call inside `ProductCarouselComponent` and derive the three values there
- [x] Remove `storeIds`, `isUserDefinedList`, and `isDefaultStores` from `ProductCarouselProps` type
- [x] Remove those props from every call site (HomePage, BargainsPage, PillarPage, ProductPage)
- [ ] Verify carousel still refetches correctly when user changes store selection

Note: `ProductCarousel` already uses `useDialog`, `usePathname`, and internal state — it must
remain `"use client"`. Making it self-contained for store state is not the same as making it a
server component.

---

## Indexable pages

These are the pages in the sitemap. Everything else (search, product, login, auth flows) can
stay CSR for now.

### `/contact`

Almost free. `ContactPage` is `"use client"` but calls no hooks and uses no browser APIs.
Its children (`Hero`, `ContactDetails`, `OtherSites`) appear to be pure display components.

- [x] Confirm `Hero`, `ContactDetails`, `OtherSites` have no hooks or browser API usage
- [x] Remove `"use client"` from `ContactPage`
- [x] Remove `"use client"` from any child components that are confirmed pure display
- [x] Confirm `src/app/contact/page.tsx` has static metadata export (already done, just verify)
- [x] Build passes, page renders

### `/` — HomePage

Blocked on the ProductCarousel refactor above.

- [x] (ProductCarousel self-contained — see critical enabler)
- [x] Remove `useStoreList()` from `HomePage`
- [x] Remove `"use client"` from `HomePage`
- [ ] Confirm static sections (hero, HowItWorks, FounderLetter, FAQ) render in initial HTML
      without client JS (check view-source or curl)
- [x] `BrowseCategoriesSection` — confirm it has no hooks and can remain server (it's pure links)
- [x] `HowItWorksSection`, `FounderLetterSection`, `FAQ` — confirm no hooks, remove `"use client"` if present
- [x] Build passes, page renders, carousel still refetches on store change

### `/bargains` — BargainsPage

`initialBargainStats` is already passed from the server route. Once ProductCarousel is
self-contained the only remaining hooks are `useStoreList()` and the `useApiQuery` for
bargainStats (which has an `initialBargainStats` fallback).

- [ ] (ProductCarousel self-contained — see critical enabler)
- [ ] Remove `useStoreList()` from `BargainsPage` 
- [ ] Remove `useApiQuery` for bargainStats — `initialBargainStats` is always provided by the
      server route; the client fetch is redundant (check `src/app/bargains/page.tsx` to confirm)
- [ ] Remove `"use client"` from `BargainsPage`
- [ ] `PriceComparisonChart` — already confirmed as a pure display component, no hooks; confirm
      and remove `"use client"` if it has one
- [ ] `FAQ` component — check for hooks; likely pure display, remove `"use client"` if present
- [ ] Build passes, stats and hero render in initial HTML, carousels still work

### `/categories/[slug]` — PillarPage

`initialPillarPage` is already passed from the server route. PillarPage uses `useParams()` for
the slug, `useStoreList()` for the carousels, and `useApiQuery` to fetch pillarPage data when
`initialPillarPage` is absent.

- [ ] (ProductCarousel self-contained — see critical enabler)
- [ ] Update `PillarPage` signature to accept `slug: string` prop instead of calling `useParams()`
- [ ] Update `src/app/categories/[slug]/page.tsx` to pass `slug` prop down to `PillarPage`
- [ ] Remove `useStoreList()` from `PillarPage`
- [ ] Remove `useApiQuery` for pillarPage — `initialPillarPage` is always provided by the server
      route (add `if (!pillarPage) notFound()` guard in the route file to match current error state)
- [ ] Remove `"use client"` from `PillarPage`
- [ ] `FaqV2` component — check for hooks; likely pure display, remove `"use client"` if present
- [ ] Add `generateStaticParams` to `src/app/categories/[slug]/page.tsx` for the 11 known slugs
      (fetch from `/api/categories/primary/` or hardcode the list)
- [ ] Build passes, hero + FAQ + comparison charts render in initial HTML

---

## Shell improvements (after indexable pages are done)

These are lower priority but complete the SSR story for repeated page furniture.

- [ ] **CategoryBar** — currently fetches `/api/categories/primary/` client-side on every page.
      Server-fetch in `src/app/layout.tsx` and pass as prop to a thin client `CategoryBar` that
      only owns the carousel scroll and router navigation behavior. The category list itself can
      then be server-rendered.

- [ ] **NavBar** — currently receives all props from `AppShell` (search state, cart total, auth).
      Split into a server wrapper for the logo/layout shell + a `"use client"` island for the
      search input, cart badge, and auth controls. This decouples the static nav chrome from the
      client bundle.

- [ ] **AppShell** — once NavBar is self-contained, `AppShell` may be reducible to a thin client
      component only responsible for the `SettingsDialog`, `Toaster`, and `NextButton`. Evaluate
      whether it can be replaced with the layout directly importing a slimmed `NavBar`.

---

## Dead code cleanup

These files exist because of the Vite-era migration. They are excluded from the TS build but
they pollute the repo.

- [x] Delete `src/App.tsx` (old React Router SPA entry — unused)
- [x] Delete `src/main.tsx` (old Vite/BrowserRouter entry — unused)
- [x] Delete `index.html` (Vite HTML entry — unused)
- [x] Delete `vite.config.ts` (unused)
- [x] Delete `tsconfig.app.json` and `tsconfig.node.json` (Vite-era configs — unused)
- [ ] Delete `dist/` directory if present (old Vite build output)
- [x] Remove from `tsconfig.json` the excludes for `App.tsx` and `main.tsx` after deletion
- [x] Remove from `package.json`: `vite`, `@vitejs/plugin-react`, `eslint-plugin-react-refresh`
- [x] Remove `react-router-dom` from `package.json` (only imported in dead `App.tsx`)
- [x] Remove `@tailwindcss/vite` from `package.json` (superseded by `@tailwindcss/postcss`)
- [x] Run `npm install` after package removals and confirm build still passes

---

## DRY and simplification

- [ ] **`Seo` component** (`src/components/Seo.tsx`) is a no-op. All props except `structuredData`
      are explicitly voided. The metadata responsibility has moved to Next.js `metadata` / 
      `generateMetadata` exports on the route files. Remove `Seo` and its usages:
      - Move any `structuredData` JSON-LD it renders into a `<script>` tag directly in the
        server route file (pattern already used in `src/app/page.tsx` and allbikes)
      - Delete `src/components/Seo.tsx` and its type `src/types/SeoProps.ts`
      - Remove all `<Seo />` JSX from page_components

- [ ] **`faqsBySlug`** in `PillarPage.tsx` is a large hardcoded map embedded in a component file.
      Extract to `src/data/pillar-faqs.ts` so `PillarPage` just imports the data. Keeps the
      component readable.

- [ ] **PillarPage image mapping** is a long if-else chain (slug → image asset). Convert to a
      plain record/map object at the top of the file or in a data module.

- [ ] **`initialCompanyProducts`** prop on `BargainsPage` — verify whether the server route
      actually passes this or if it was planned but not wired. If unused, remove the prop.

- [ ] **`NavBarProps`** type — if NavBar becomes self-contained after the shell improvements
      above, this type becomes dead. Remove it when that work lands.

---

## Acceptance criteria for each indexable page

Before marking a page done:

1. `curl` or view-source shows real `<h1>`, body copy, and structured data in the HTML response
   without any JavaScript execution.
2. The page_component file no longer has `"use client"` at the top.
3. Interactive features (carousel scroll, store selection, cart) still work after hydration.
4. `npm run build` passes with no new type errors.
5. The route still appears in `sitemap.xml`.
