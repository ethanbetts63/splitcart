/**
 * Copied from `freethedesk/frontend/scripts/seo/app-routes.mjs`, unchanged.
 *
 * Route discovery for the SEO checks: what the App Router actually serves.
 *
 * Shared by `indexation-ledger.mjs` and `sitemap-routes.mjs` so the two can
 * never disagree about what a route is — they are two halves of one question
 * (every route declared, every declaration real) and a difference in how they
 * enumerate the tree would show up as a phantom failure in one of them.
 */
import { readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

/**
 * Every `page.tsx` in the app tree, as a route: groups stripped, `/` for the
 * root. Returns route → absolute file path.
 */
export function discoverRoutes(appDir, segments = []) {
  const found = new Map();
  for (const entry of readdirSync(appDir)) {
    const full = join(appDir, entry);
    if (statSync(full).isDirectory()) {
      // `(catalog)` and friends are organisational, not part of the URL.
      const next = /^\(.*\)$/.test(entry) ? segments : [...segments, entry];
      for (const [route, file] of discoverRoutes(full, next)) found.set(route, file);
    } else if (entry === 'page.tsx') {
      found.set(`/${segments.join('/')}`.replace(/\/$/, '') || '/', full);
    }
  }
  return found;
}

/**
 * Resolve a concrete route to the page that serves it, following dynamic
 * segments. `/articles/best-flower-delivery-perth` is served by
 * `/articles/[slug]`; bloomprint spreads a registry entry per article into
 * `STATIC_PAGES`, so most of what it declares has no literal page of its own.
 *
 * An exact match always wins over a dynamic one, which is Next's own
 * precedence. Returns the page file, or `undefined`.
 */
export function resolveRoute(routes, route) {
  const exact = routes.get(route);
  if (exact) return exact;

  const parts = route.split('/').filter(Boolean);

  for (const [candidate, file] of routes) {
    const segments = candidate.split('/').filter(Boolean);
    const catchAll = segments.at(-1)?.startsWith('[...');

    if (catchAll ? parts.length < segments.length : parts.length !== segments.length) continue;

    const matched = segments.every((segment, index) => {
      if (segment.startsWith('[')) return true;
      return segment === parts[index];
    });

    if (matched) return file;
  }

  return undefined;
}
