/**
 * Fails the build when the sitemap-listed registry drifts from the app tree (the outward counterpart of
 * `indexation-ledger.mjs`):
 *
 *  - A listed route that no longer resolves to a page wastes crawl budget advertising a 301.
 *  - A listed route whose page is only a `redirect`/`permanentRedirect` stub: list the destination, not the hop.
 *
 *  - A listed route whose `updated` is not a YYYY-MM-DD date, which would reach `new Date()` and emit `Invalid Date`
 *    into the XML. `lastmod` is the registry's date and nothing else: never the build time, never one literal copied
 *    across every entry (splitcart shipped fourteen of those).
 *
 * `STATIC_PAGES` is imported, not scraped: bloomprint spreads one entry per article into it at module evaluation,
 * so many listed routes are not literal keys in the source. A repo whose sitemap also lists a dynamic family passes
 * `extraEntries` to name those URLs from the same module `app/sitemap.ts` reads them from.
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
 * @param {(pages: object) => [string, string][]} [options.extraEntries] Further `[route, updated]` pairs the sitemap
 *   emits, read from the imported `lib/pages.ts`.
 */
export async function checkSitemapRoutes({ root, extraEntries = () => [] }) {
  const src = join(root, 'src');
  registerTsLoader(src);

  const pages = await import(pathToFileURL(join(src, 'lib/pages.ts')).href);
  const entries = [
    ...Object.entries(pages.STATIC_PAGES).map(([route, page]) => [route, page.updated]),
    ...extraEntries(pages),
  ];
  const declared = entries.map(([route]) => route);
  const routes = discoverRoutes(join(src, 'app'));

  const failures = [];

  if (!declared.length) {
    failures.push('STATIC_PAGES is empty — has the registry changed shape?');
  }

  const missing = declared.filter((route) => !resolveRoute(routes, route));
  if (missing.length) {
    failures.push(
      `These routes are in the sitemap but have no page in src/app:\n    ${missing.join('\n    ')}\n` +
        '  Remove them, or restore the page.',
    );
  }

  const redirects = declared.filter((route) => {
    const file = resolveRoute(routes, route);
    return file && REDIRECT_STUB.test(readFileSync(file, 'utf8'));
  });
  if (redirects.length) {
    failures.push(
      `These routes are in the sitemap but their page only redirects:\n    ${redirects.join('\n    ')}\n` +
        '  A sitemap should list the destination, not the hop.',
    );
  }

  const badDates = entries
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
    `check-sitemap-routes: all ${declared.length} listed routes resolve to real pages with a real date.`,
  );
}
