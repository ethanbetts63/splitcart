/**
 * Fails the build when what the sitemap advertises drifts from the app tree.
 *
 * Adapted from `freethedesk/frontend/scripts/seo/sitemap-routes.mjs`. SplitCart
 * is not a component-registry consumer yet (`_docs/convergence/registry.md`),
 * so this is a local copy. Two deliberate local additions, marked below: it
 * also walks the category pillar pages, which are a dynamic family rather than
 * `STATIC_PAGES` entries but are still in the sitemap; and it asserts every
 * `lastmod` date it will emit is a real ISO date, because those dates were the
 * original defect here — fourteen hardcoded entries all carrying one
 * copy-pasted literal.
 *
 * `indexation-ledger.mjs` guards the inward direction — a route nobody
 * declared. This is the outward direction, and it catches the half that
 * silently costs traffic:
 *
 *  - A listed route that no longer resolves to a page, so the sitemap spends
 *    crawl budget advertising a 404 or a redirect.
 *  - A listed route whose page is only a `redirect`/`permanentRedirect` stub. A
 *    sitemap should list the destination, not the hop.
 *
 * The registry is imported rather than scraped, so formatting, quoting style
 * and computed entries all stop being load-bearing.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { registerTsLoader } from './ts-loader.mjs';
import { discoverRoutes, resolveRoute } from './app-routes.mjs';

const REDIRECT_STUB = /\bpermanentRedirect\s*\(|\bredirect\s*\(/;
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

/**
 * @param {object} options
 * @param {string} options.root Absolute path to the repo's `frontend`.
 */
export async function checkSitemapRoutes({ root }) {
  const src = join(root, 'src');
  registerTsLoader(src);

  const pages = await import(pathToFileURL(join(src, 'lib/pages.ts')).href);

  /**
   * Local addition: every URL the sitemap emits, not just `STATIC_PAGES`.
   * `app/sitemap.ts` builds its category half from `CATEGORY_PAGE_UPDATED`, so
   * this reads the same object rather than a second list of slugs.
   */
  const declared = [
    ...Object.entries(pages.STATIC_PAGES).map(([path, page]) => [path, page.updated]),
    ...Object.entries(pages.CATEGORY_PAGE_UPDATED).map(([slug, updated]) => [
      `/categories/${slug}`,
      updated,
    ]),
  ];

  const routes = discoverRoutes(join(src, 'app'));
  const failures = [];

  if (!Object.keys(pages.STATIC_PAGES).length) {
    failures.push('STATIC_PAGES is empty — has the registry changed shape?');
  }

  const missing = declared
    .filter(([route]) => !resolveRoute(routes, route))
    .map(([route]) => route);
  if (missing.length) {
    failures.push(
      `These routes are in the sitemap but have no page in src/app:\n    ${missing.join('\n    ')}\n` +
        '  Remove them, or restore the page.',
    );
  }

  const redirects = declared
    .filter(([route]) => {
      const file = resolveRoute(routes, route);
      return file && REDIRECT_STUB.test(readFileSync(file, 'utf8'));
    })
    .map(([route]) => route);
  if (redirects.length) {
    failures.push(
      `These routes are in the sitemap but their page only redirects:\n    ${redirects.join('\n    ')}\n` +
        '  A sitemap should list the destination, not the hop.',
    );
  }

  // Local addition. `lastModified` is the registry's `updated` and nothing
  // else — never the build time, never a literal copied across every entry.
  // A value that is not an ISO date would reach `new Date()` and emit
  // `Invalid Date` into the XML.
  const badDates = declared
    .filter(([, updated]) => !ISO_DATE.test(String(updated ?? '')))
    .map(([route, updated]) => `${route} — ${JSON.stringify(updated)}`);
  if (badDates.length) {
    failures.push(
      `${badDates.length} route(s) with an unusable sitemap date:\n    ${badDates.join('\n    ')}\n` +
        '  `updated` must be a YYYY-MM-DD date, bumped in the same commit as the page.',
    );
  }

  if (failures.length) {
    console.error('\ncheck-sitemap-routes failed:\n');
    for (const failure of failures) console.error(`• ${failure}\n`);
    process.exit(1);
  }

  console.log(
    `check-sitemap-routes: all ${declared.length} sitemap routes resolve to real pages with a real date.`,
  );
}
