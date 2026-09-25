/**
 * The site origin and the handful of constants derived straight from it.
 *
 * This module is a leaf on purpose: it imports nothing, so `sitemap.ts`,
 * `robots.txt/route.ts` and `lib/pages.ts` can take the origin without dragging
 * `lib/seo.ts` into a statically-rendered route's module graph — and so a
 * build-time check can load any of them. See seo-standard.md section 5.
 *
 * Before this file existed the origin was spelled four independent times:
 * `siteUrl` in `lib/seo.ts`, `baseUrl` in `app/sitemap.ts`, a bare string
 * literal in `app/robots.ts` and a fourth copy inside `metadataBase` in
 * `app/layout.tsx`. Four copies is four chances to disagree, and the sitemap
 * and the canonical tags had already disagreed on the category routes.
 *
 * Define the origin exactly once. An inline
 * `process.env.NEXT_PUBLIC_SITE_URL ?? '…'` anywhere else is a second origin
 * that will drift from this one.
 */

/**
 * The canonical host. `www` rather than the apex, because that is what the
 * deployed site serves and what every indexed URL already spells.
 */
export const SITE_URL = (
  process.env.NEXT_PUBLIC_SITE_URL ?? 'https://www.splitcart.com.au'
).replace(/\/$/, '');

/** The site's name in `siteName`, in the `WebSite` node, and in the OG card. */
export const SITE_NAME = 'SplitCart';

/**
 * The one fallback link-preview image, and its real dimensions.
 *
 * Only the default asset carries width and height: a page-supplied image would
 * be a photograph whose size the metadata builder does not know, and stating it
 * wrongly is worse than omitting it. `check:og-images` asserts this path exists
 * in `public/` — it pointed at a file that never existed until 2026-09-25.
 */
export const DEFAULT_OG_IMAGE = '/og-default.png';
export const DEFAULT_OG_WIDTH = 1200;
export const DEFAULT_OG_HEIGHT = 630;

/**
 * The site's logo as a schema.org `Organization.logo`. Google wants a
 * crawlable raster it can show beside the entity; the 512px favicon is the
 * only mark this repo ships, and it is the same one the tab and the OG card
 * use, so the three agree.
 */
export const ORGANIZATION_LOGO = '/favicon-512x512.png';

/**
 * The address on the contact page and in `llms.txt`. One spelling, so the
 * visible copy and the `ContactPoint` node cannot contradict each other.
 */
export const CONTACT_EMAIL = 'ethanbetts63@gmail.com';

/**
 * Stable `@id`s for the two nodes every other node points at.
 *
 * `@id` is never resolved across sites — it is an identifier inside this
 * graph — so these only have to be stable and unique here. See seo-standard.md
 * section 3.
 */
export const ORGANIZATION_ID = `${SITE_URL}#organization`;
export const WEBSITE_ID = `${SITE_URL}#website`;
