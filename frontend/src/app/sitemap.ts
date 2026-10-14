import type { MetadataRoute } from 'next';

import { CATEGORY_SLUGS } from '@/data/categories';
import { fetchCatalogue } from '@/lib/catalogue';
import { CATEGORY_PAGE_UPDATED, STATIC_PAGES } from '@/lib/pages';
import { absoluteUrl } from '@/lib/seo';

/**
 * Every registry route, the eleven category pillar pages, and every indexable
 * product page.
 *
 * This file used to be fourteen hardcoded objects, all fourteen carrying the
 * same literal `lastModified: "2026-06-29"` — the day the file was written and
 * never touched since. A permanently stale date is worse than build time, which
 * at least changes; both teach Google to ignore every date in the file. The
 * dates now come from the registry's `updated`, which is a required field and a
 * maintenance obligation: change a page, bump it in the same commit.
 *
 * No `changeFrequency` and no `priority`. Google has ignored both for years.
 *
 * URLs come from `absoluteUrl`, the same helper the canonical tag uses, so the
 * sitemap and the `<head>` cannot spell a route two ways. They did: the
 * category entries here carried a trailing slash while the pages' own
 * canonicals did not.
 *
 * `updated` goes into `<lastmod>` as the bare `YYYY-MM-DD` it already is, not
 * via `new Date()`. A W3C date is a legal `<lastmod>` value, and converting to
 * a timestamp first would emit Perth midnight as `…T16:00:00.000Z` — the
 * previous calendar day in UTC, so the file would say 28 June for a page the
 * registry says changed on the 29th. One date, spelled the same in both places.
 *
 * Product pages carry no `lastmod`. Nothing records when a product's prices
 * last changed — a scrape re-dates every price whether it moved or not — and a
 * date that moves without the page changing is the stale-date problem above in
 * another form. The set is Django's (`/api/products/indexable/`, the same rule
 * that sets each page's robots tag), refreshed daily like the pages themselves.
 */
export const revalidate = 86400;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticPages = Object.entries(STATIC_PAGES).map(
    ([path, page]): MetadataRoute.Sitemap[number] => ({
      url: absoluteUrl(path),
      lastModified: page.updated,
    }),
  );

  const categoryPages = CATEGORY_SLUGS.map((slug): MetadataRoute.Sitemap[number] => ({
    url: absoluteUrl(`/categories/${slug}`),
    lastModified: CATEGORY_PAGE_UPDATED[slug],
  }));

  const indexable =
    (await fetchCatalogue<{ slug: string }[]>('/api/products/indexable/', revalidate)) ?? [];
  const productPages = indexable.map(({ slug }): MetadataRoute.Sitemap[number] => ({
    url: absoluteUrl(`/product/${slug}`),
  }));

  return [...staticPages, ...categoryPages, ...productPages];
}
