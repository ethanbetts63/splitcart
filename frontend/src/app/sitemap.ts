import type { MetadataRoute } from 'next';

import { CATEGORY_SLUGS } from '@/data/categories';
import { CATEGORY_PAGE_UPDATED, STATIC_PAGES } from '@/lib/pages';
import { absoluteUrl } from '@/lib/seo';

/**
 * Every registry route, plus the eleven category pillar pages.
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
 * Perth time (+08:00) rather than UTC, so a date does not read as the previous
 * evening.
 */
const asDate = (updated: string) => new Date(`${updated}T00:00:00+08:00`);

export default function sitemap(): MetadataRoute.Sitemap {
  const staticPages = Object.entries(STATIC_PAGES).map(
    ([path, page]): MetadataRoute.Sitemap[number] => ({
      url: absoluteUrl(path),
      lastModified: asDate(page.updated),
    }),
  );

  const categoryPages = CATEGORY_SLUGS.map((slug): MetadataRoute.Sitemap[number] => ({
    url: absoluteUrl(`/categories/${slug}`),
    lastModified: asDate(CATEGORY_PAGE_UPDATED[slug]),
  }));

  return [...staticPages, ...categoryPages];
}
