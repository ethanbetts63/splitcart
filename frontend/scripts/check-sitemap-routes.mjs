#!/usr/bin/env node
/** Thin entry point over `scripts/seo/sitemap-routes.mjs`. */
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkSitemapRoutes } from './seo/sitemap-routes.mjs';

await checkSitemapRoutes({
  root: join(dirname(fileURLToPath(import.meta.url)), '..'),
  // The category pillar pages are a dynamic family, not `STATIC_PAGES` entries,
  // but `app/sitemap.ts` lists them, dated from this same object.
  extraEntries: (pages) =>
    Object.entries(pages.CATEGORY_PAGE_UPDATED).map(([slug, updated]) => [
      `/categories/${slug}`,
      updated,
    ]),
});
