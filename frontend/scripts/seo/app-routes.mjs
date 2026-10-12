/** Route discovery for the SEO checks, shared by `indexation-ledger.mjs` and `sitemap-routes.mjs` so they cannot disagree about what a route is. */
import { readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

/** Every `page.tsx` in the app tree as a route (groups stripped, `/` for the root): route → absolute file path. */
export function discoverRoutes(appDir, segments = []) {
  const found = new Map();
  for (const entry of readdirSync(appDir)) {
    const full = join(appDir, entry);
    if (statSync(full).isDirectory()) {
      // `(group)` directories are not part of the URL.
      const next = /^\(.*\)$/.test(entry) ? segments : [...segments, entry];
      for (const [route, file] of discoverRoutes(full, next)) found.set(route, file);
    } else if (entry === 'page.tsx') {
      found.set(`/${segments.join('/')}`.replace(/\/$/, '') || '/', full);
    }
  }
  return found;
}

/**
 * Resolves a concrete route to the page serving it, following dynamic segments (`/articles/some-slug` is served by
 * `/articles/[slug]`). An exact match beats a dynamic one, as in Next. Returns the page file or `undefined`.
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
