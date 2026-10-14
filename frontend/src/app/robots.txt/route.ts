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
  // Password reset links. Each path carries a one-time credential, so it is a
  // capability URL: nothing to crawl, and nothing a crawler should hold.
  '/reset-password',
  // An unbounded query surface: every distinct `?q=` is a new URL and none of
  // them is worth a crawl.
  '/search',
];

/**
 * `/product` is deliberately NOT here, since 2026-10-14. Each product page is
 * indexable or `noindex` by its own record (`app/product/[slug]/page.tsx`), and
 * a crawler has to fetch a page to read that. It was disallowed on origin load;
 * the page's one-day revalidation is what bounds that now.
 */

/**
 * `/login`, `/signup`, `/forgot-password`, `/final-cart` and `/substitutions`
 * are deliberately NOT here. They are noindex instead (`STATIC_NOINDEX_PAGES` in `lib/pages.ts`),
 * because noindex only works on a page that is crawled. Until 2026-09-25 they
 * were both disallowed and noindexed, which meant Google never fetched them,
 * never read the directive, and could still surface them as bare titleless
 * URLs. A few bounded application pages cost nothing to let a crawler read.
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
 * Two of the exclusions are the shared standard's "capability URLs and the API
 * only"; the third is a deliberate local divergence from it:
 *   - `/api` — the proxy, not content, same as for everyone.
 *   - `/reset-password` — capability URLs, same as for everyone.
 *   - `/search` — genuinely unbounded, and a dead end for any crawler.
 *
 * `DISALLOWED_ROUTES` stays the authoritative list for everything that is not
 * robots.txt: the indexation ledger resolves state 4 from the `*` group alone.
 */
const AI_DISALLOWED_ROUTES = ['/api', '/reset-password', '/search'];

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
