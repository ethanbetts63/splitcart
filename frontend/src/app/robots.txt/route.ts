import { SITE_URL } from '@/lib/siteConfig';

/**
 * robots.txt as a text route rather than Next's typed `robots.ts`.
 *
 * `MetadataRoute.Robots` can only emit directives, and the llms.txt pointer has
 * to be a comment — robots.txt has no directive for it, so every consumer that
 * looks for one reads it out of a comment line. SplitCart has shipped
 * `public/llms.txt` all along and never pointed at it. The rules themselves
 * stay in a typed object so they are still checkable; only the serialisation is
 * ours, and `check-indexation-ledger.mjs` reads the bytes this `GET()` returns
 * rather than guessing at the source. See seo-standard.md section 4 (SEO-8).
 */

interface RobotsGroup {
  userAgents: string[];
  allow: string[];
  disallow: string[];
}

/**
 * Staff surfaces and unbounded generated ones.
 *
 * Every entry is the BARE prefix, never the trailing-slash form. Robots rules
 * are prefixes, so `/admin` already covers `/admin/` and everything under it,
 * while `/admin/` does NOT match the exact path `/admin` — the gap this file
 * shipped with on four of its eight rules (`/admin/`, `/api/`,
 * `/substitutions/`, `/final-cart/`).
 *
 * No `$` anchoring anywhere: it is a Google and Bing extension, not part of
 * RFC 9309, and a conforming parser reads it as a literal character and matches
 * nothing.
 */
const DISALLOWED_ROUTES = [
  // Django admin and the API proxy. Neither is a page.
  '/admin',
  '/api',
  // An unbounded query surface: every distinct `?q=` is a new URL and none of
  // them is worth a crawl.
  '/search',
  // Tens of thousands of generated pages, each served by a live fetch against
  // the Django API. Disallow rather than noindex, because noindex would require
  // crawling all of them to take effect — which is the cost being avoided.
  '/product',
];

/**
 * `/login`, `/signup`, `/final-cart` and `/substitutions` are deliberately NOT
 * here. They are noindex instead (`STATIC_NOINDEX_PAGES` in `lib/pages.ts`),
 * because noindex only works on a page that is crawled. Until 2026-09-25 they
 * were both disallowed and noindexed, which meant Google never fetched them,
 * never read the directive, and could still surface them as bare titleless
 * URLs. Four bounded application pages cost nothing to let a crawler read.
 */

const AI_USER_AGENTS = [
  'GPTBot',
  'OAI-SearchBot',
  'ChatGPT-User',
  'ClaudeBot',
  'Claude-Web',
  'anthropic-ai',
  'PerplexityBot',
  'Google-Extended',
  'CCBot',
];

/**
 * Answer engines get the whole public site, minus three prefixes.
 *
 * Being cited is the point of publishing the pillar pages and the bargain data,
 * and an answer engine fetching a login form costs one wasted request. So the
 * `*` list's crawl-budget reasoning does not transfer wholesale.
 *
 * Three exclusions survive it, and they are a deliberate local divergence from
 * the shared standard's "capability URLs and the API only":
 *   - `/api` — the proxy, not content, same as for everyone.
 *   - `/search` — genuinely unbounded, and a dead end for any crawler.
 *   - `/product` — the reason here is not crawl budget, it is origin load. Each
 *     of those pages is a live API fetch against one small Django instance, and
 *     there are tens of thousands of them. SplitCart has also decided those
 *     pages stay out of search; opening them to answer engines alone would
 *     contradict that decision rather than refine it.
 *
 * `DISALLOWED_ROUTES` stays the authoritative list for everything that is not
 * robots.txt: the indexation ledger resolves state 4 from the `*` group alone.
 */
const AI_DISALLOWED_ROUTES = ['/api', '/search', '/product'];

const GROUPS: RobotsGroup[] = [
  { userAgents: ['*'], allow: ['/'], disallow: DISALLOWED_ROUTES },
  { userAgents: AI_USER_AGENTS, allow: ['/'], disallow: AI_DISALLOWED_ROUTES },
];

function renderGroup(group: RobotsGroup): string {
  return [
    ...group.userAgents.map((agent) => `User-Agent: ${agent}`),
    ...group.allow.map((path) => `Allow: ${path}`),
    ...group.disallow.map((path) => `Disallow: ${path}`),
  ].join('\n');
}

function renderRobotsTxt(): string {
  return `${[
    ...GROUPS.map(renderGroup),
    [
      `Sitemap: ${SITE_URL}/sitemap.xml`,
      // Not a directive — no crawler acts on this line. It is a signpost for
      // anyone reading robots.txt to find the site summary at its well-known
      // path.
      `# llms.txt: ${SITE_URL}/llms.txt`,
    ].join('\n'),
  ].join('\n\n')}\n`;
}

// Nothing here reads the request, so the body is built once at build time.
export const dynamic = 'force-static';

export function GET(): Response {
  return new Response(renderRobotsTxt(), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
