import type { Metadata } from 'next';

import type { CategorySlug } from '@/data/categories';

/**
 * The page registry: seo-standard.md section 1.
 *
 * Every hand-authored indexable route is exactly one record here, and this is
 * the single source for its `<title>`, its meta/OG description and its sitemap
 * `lastmod`. Before this file existed, each `page.tsx` passed inline strings to
 * `createMetadata()` and the sitemap hardcoded a parallel list of URLs carrying
 * one copy-pasted date — so nothing could compare the two, and they had already
 * drifted (`/privacy` was indexable and in no sitemap at all).
 *
 * This module is loaded by build-time checks (`check-sitemap-routes.mjs`,
 * `check-indexation-ledger.mjs`), so it must stay free of import-time side
 * effects and of anything that needs a request context. It is plain data and
 * one type-only import; keep it that way.
 */
export interface StaticPage {
  /**
   * ISO date of the last material content change; emitted as `dateModified`
   * and as the sitemap's `<lastmod>`.
   *
   * Required, not optional. Nothing can derive this — git history is flat and
   * there is no route-to-query mapping a sitemap could re-derive a date from —
   * so the rule is: change a page, bump its date in the same commit. Required
   * rather than optional is what makes `tsc` refuse a new page without one.
   */
  updated: string;

  title: string;
  description: string;

  /**
   * Short name for the final breadcrumb crumb. Breadcrumbs are rendered by
   * Google, so they need a plain label; the SEO `title` carries a keyword tail
   * that reads as noise in a trail.
   */
  label?: string;

  /**
   * Skip the `%s | SplitCart` title template from `layout.tsx`.
   *
   * Set on the two pages whose title already says SplitCart. Without it the
   * homepage rendered `<title>SplitCart: Australian Grocery Price Comparison |
   * SplitCart</title>` — the template applies to any plain-string title, and
   * nothing was opting out.
   */
  absoluteTitle?: boolean;
}

export const STATIC_PAGES = {
  '/': {
    updated: '2026-06-29',
    label: 'Home',
    title: 'SplitCart: Australian Grocery Price Comparison',
    description:
      'Every store has a deal, but finding them all takes forever. SplitCart compares prices across Coles, Woolworths, and Aldi and splits your cart for the cheapest overall shop.',
    absoluteTitle: true,
  },
  '/bargains': {
    updated: '2026-06-29',
    label: 'Bargains',
    title: "SplitCart: Australia's Best Grocery Bargains",
    description:
      'Find the best grocery bargains in Australia. SplitCart compares prices across Coles, Woolworths, and Aldi to find you the biggest discounts.',
    absoluteTitle: true,
  },
  '/contact': {
    updated: '2026-06-29',
    label: 'Contact',
    title: 'Contact Us',
    description: 'Have questions, suggestions, or feedback? Get in touch with SplitCart.',
  },
  '/privacy': {
    updated: '2026-05-11',
    label: 'Privacy Policy',
    title: 'Privacy Policy',
    description:
      'Read the SplitCart privacy policy, including what information is collected and how it is used.',
  },
} as const satisfies Record<string, StaticPage>;

export type PagePath = keyof typeof STATIC_PAGES;

/**
 * Category pillar pages are data-driven — their title and description come from
 * the Django `pillar-pages` record, not from a literal here — so they are a
 * dynamic family rather than registry entries (seo-standard.md section 1). What
 * they still need is a `lastmod` a sitemap can emit, and no date exists in the
 * underlying record, so it is hand-maintained here.
 *
 * `Record<CategorySlug, string>` rather than a second list of slugs: the slug
 * set is declared exactly once, as `CATEGORY_SLUGS` in `data/categories.ts`,
 * and the compiler refuses this object if it covers a different set. Adding a
 * category without a date, or leaving a date behind after removing one, is a
 * type error rather than a silent sitemap gap.
 */
export const CATEGORY_PAGE_UPDATED: Record<CategorySlug, string> = {
  'snacks-and-sweets': '2026-06-29',
  // FAQ copy rewritten 2026-09-25 to stop publishing undated price figures.
  'meat-and-seafood': '2026-09-25',
  'dairy-and-eggs': '2026-06-29',
  'fruit-and-veg': '2026-09-25',
  pantry: '2026-06-29',
  'international-herbs-and-spices': '2026-06-29',
  'bakery-and-deli': '2026-06-29',
  drinks: '2026-06-29',
  'health-beauty-and-supplements': '2026-06-29',
  'home-cleaning-gardening-and-pets': '2026-06-29',
  baby: '2026-06-29',
};

/**
 * Static routes that are crawlable but not indexable — state 3 of
 * seo-standard.md section 2.
 *
 * Each one's `page.tsx` must `export const metadata = NOINDEX_METADATA`, and
 * `check-indexation-ledger.mjs` fails the build when one does not: listing a
 * route here is not what makes it noindexed, and a ledger that only checks the
 * decision was recorded is worse than none.
 *
 * Noindex rather than a robots.txt disallow, because noindex only works on a
 * page that is crawled. All four were previously BOTH noindexed and disallowed,
 * which the standard forbids: the disallow meant Google never read the noindex,
 * so they could still surface as bare titleless URLs. These are a handful of
 * bounded application pages, so letting a crawler fetch them and read the
 * directive costs nothing worth counting.
 */
export const STATIC_NOINDEX_PAGES: string[] = [
  '/login',
  '/signup',
  '/forgot-password',
  '/final-cart',
  '/substitutions',
];

/** What a route in `STATIC_NOINDEX_PAGES` must export for that to be true. */
export const NOINDEX_METADATA: Metadata = {
  title: { absolute: 'SplitCart' },
  robots: { index: false, follow: false },
};

/**
 * Routes whose page only redirects. Empty: SplitCart's four legacy
 * `/pillar-pages/*` redirects are declared in `next.config.ts`, so they have no
 * `page.tsx` in the app tree and the indexation ledger never sees them.
 */
export const REDIRECT_STUBS: string[] = [];

/**
 * Route families generated from data rather than hand-authored, one entry per
 * distinct dynamic `page.tsx`.
 *
 * `policyModule`/`policySymbol` are a module path plus a symbol rather than a
 * function reference, so the ledger can assert both still exist without
 * importing a module that reaches the API client.
 */
export interface DynamicRouteFamily {
  /** The route as it appears in the app tree, dynamic segments included. */
  pattern: string;
  /** One of the four ledger states, or 'conditional' when it varies by record. */
  state: 'listed' | 'unlisted' | 'noindex' | 'conditional';
  /** Where the real per-record decision is made, relative to `src/`. */
  policyModule: string;
  /** A named export, or any distinctive line, inside `policyModule`. */
  policySymbol?: string;
  /** Why it resolves the way it does. Prose, for a human. */
  policyNote?: string;
}

export const DYNAMIC_ROUTE_FAMILIES: DynamicRouteFamily[] = [
  {
    pattern: '/categories/[slug]',
    state: 'listed',
    policyModule: 'data/categories.ts',
    policySymbol: 'CATEGORY_SLUGS',
    policyNote:
      'A closed set of 11 pillar pages, every one of them listed. The slugs are ' +
      'the family; their titles and descriptions come from the Django pillar-page ' +
      'record, and their sitemap dates from CATEGORY_PAGE_UPDATED above.',
  },
  {
    pattern: '/product/[slug]',
    state: 'conditional',
    policyModule: 'app/product/[slug]/page.tsx',
    policySymbol: 'noindex: !product.indexable',
    policyNote:
      'Indexable when at least two of Aldi, Coles and Woolworths have a current ' +
      'price for the product (Django, products/utils/indexable.py); noindex ' +
      'otherwise. app/sitemap.ts lists exactly the indexable set, from the same rule.',
  },
];

/**
 * Breadcrumb trail for a registry route, with the short `label` as the final
 * crumb. Segments that are not real pages are dropped — publishing a crumb that
 * 404s is worse than a shorter trail.
 */
export function breadcrumbItemsFor(path: PagePath): { name: string; path: string }[] {
  const page: StaticPage = STATIC_PAGES[path];
  const crumbs: { name: string; path: string }[] = [{ name: STATIC_PAGES['/'].label, path: '/' }];
  if (path === '/') return crumbs;
  crumbs.push({ name: page.label ?? page.title, path });
  return crumbs;
}
