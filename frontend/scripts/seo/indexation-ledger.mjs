/**
 * Copied from `freethedesk/frontend/scripts/seo/indexation-ledger.mjs`.
 * SplitCart is not a component-registry consumer yet
 * (`_docs/convergence/registry.md`), so this is a local copy rather than a
 * synced one. Unchanged from the original.
 *
 * Asserts that every public route carries exactly one true indexation policy.
 *
 * `check-sitemap-routes.mjs` guards the outward direction — a listed route with
 * no page. This is the inward direction: a new public route nobody added to any
 * bucket, which is otherwise indistinguishable from a forgotten one. Every
 * route must land in exactly one of:
 *
 *   - `STATIC_PAGES`           (lib/pages.ts)            — listed
 *   - `STATIC_NOINDEX_PAGES`   (lib/pages.ts)            — noindex
 *   - `REDIRECT_STUBS`         (lib/pages.ts)            — redirect only
 *   - `DYNAMIC_ROUTE_FAMILIES` (lib/pages.ts)            — generated from data
 *   - the robots.txt `*` group                           — disallowed
 *
 * *Exactly* one, not at least one. seo-standard.md section 2 forbids a route
 * being both disallowed and noindexed: a disallowed page is never crawled, so
 * its noindex is never read, and it can still surface as a bare URL with no
 * title.
 *
 * Both sides are read as VALUES, not as source text. The registry is imported
 * (see ts-loader.mjs) and robots.txt is taken from the route's own `GET()`, so
 * what this checks is the bytes a crawler receives rather than a regex's guess
 * at what the file says. Formatting, quoting style, comments and computed
 * entries all stop being load-bearing.
 *
 * State 4 resolves from the `*` group alone. The AI group is deliberately more
 * permissive (seo-standard.md section 4); reading the union would make a page
 * opened to answer engines look undeclared.
 *
 * A dynamic family's per-record correctness cannot be evaluated here — it
 * depends on data this has no access to. What can be checked is that the
 * family still points at something real: `policyModule` exists, and
 * `policySymbol` still appears in it. That is the rot the field was previously
 * open to, a resolver renamed with its declaration left behind.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { registerTsLoader } from './ts-loader.mjs';
import { discoverRoutes } from './app-routes.mjs';

/**
 * Split robots.txt into groups. A group is one or more consecutive
 * `User-Agent:` lines followed by its rules; the next `User-Agent:` after a
 * rule starts a new one (RFC 9309 section 2.2.1). Blank lines are not the
 * delimiter, so this holds even if the emitter stops putting them in.
 */
function parseRobots(text) {
  const groups = [];
  let current = null;
  let afterRule = false;

  for (const raw of text.split('\n')) {
    const line = raw.replace(/#.*$/, '').trim();
    if (!line) continue;

    const [field, ...rest] = line.split(':');
    const key = field.trim().toLowerCase();
    const value = rest.join(':').trim();

    if (key === 'user-agent') {
      if (!current || afterRule) {
        current = { userAgents: [], allow: [], disallow: [] };
        groups.push(current);
        afterRule = false;
      }
      current.userAgents.push(value);
    } else if ((key === 'allow' || key === 'disallow') && current) {
      if (value) current[key].push(value);
      afterRule = true;
    }
  }

  return groups;
}

/**
 * Robots.txt matching, RFC 9309 section 2.2.2: every allow and disallow rule is
 * a prefix, and the LONGEST matching rule wins. Modelling that rather than "any
 * disallow matches" is what lets an `Allow:` carve an exception out of a
 * broader `Disallow:` — and it is the same resolution a crawler performs, so
 * the ledger and robots.txt cannot disagree.
 */
function longestMatch(rules, route) {
  let best = -1;
  for (const rule of rules) {
    const trimmed = rule.replace(/\/$/, '');
    if (route === trimmed || route.startsWith(rule)) best = Math.max(best, rule.length);
  }
  return best;
}

/**
 * @param {object} options
 * @param {string} options.root       Absolute path to the repo's `frontend`.
 * @param {RegExp} options.noindexIn  Matches a page whose metadata really is noindex.
 * @param {string} options.noindexFix One line telling the author how to fix it.
 */
export async function checkIndexationLedger({ root, noindexIn, noindexFix }) {
  const src = join(root, 'src');
  registerTsLoader(src);

  const pages = await import(pathToFileURL(join(src, 'lib/pages.ts')).href);
  const robotsModule = await import(pathToFileURL(join(src, 'app/robots.txt/route.ts')).href);

  const listed = Object.keys(pages.STATIC_PAGES);
  const noindexed = pages.STATIC_NOINDEX_PAGES;
  const redirects = pages.REDIRECT_STUBS;
  const families = pages.DYNAMIC_ROUTE_FAMILIES.map((family) => family.pattern);

  const robotsText = await robotsModule.GET().text();
  const wildcard = parseRobots(robotsText).find((group) => group.userAgents.includes('*'));
  if (!wildcard) {
    throw new Error('robots.txt has no `User-Agent: *` group — every crawler is unconstrained.');
  }

  const isDisallowed = (route) =>
    longestMatch(wildcard.disallow, route) > longestMatch(wildcard.allow, route);

  const routes = discoverRoutes(join(src, 'app'));
  const undeclared = [];
  const doubleDeclared = [];

  for (const route of routes.keys()) {
    const buckets = [
      listed.includes(route) && 'STATIC_PAGES',
      noindexed.includes(route) && 'STATIC_NOINDEX_PAGES',
      redirects.includes(route) && 'REDIRECT_STUBS',
      families.includes(route) && 'DYNAMIC_ROUTE_FAMILIES',
      isDisallowed(route) && 'robots.txt Disallow',
    ].filter(Boolean);

    if (buckets.length === 0) undeclared.push(route);
    else if (buckets.length > 1) doubleDeclared.push(`${route} — ${buckets.join(' + ')}`);
  }

  // A noindex declaration is only true if the page's metadata actually carries
  // it. A route can sit in STATIC_NOINDEX_PAGES while its page emits no robots
  // meta at all, and a ledger that only checks a decision was recorded is worse
  // than none — it turns an unknown into a false assurance.
  //
  // This one assertion is still a regex over source text, because `page.tsx`
  // cannot be imported: Node strips types but does not transpile JSX. It is
  // therefore the weakest check here — a match inside a comment would satisfy
  // it. seo-standard.md section 2 records that limit.
  const unenforced = [];
  for (const route of noindexed) {
    const file = routes.get(route);
    if (!file) {
      unenforced.push(`${route} — declared noindex but has no page`);
    } else if (!noindexIn.test(readFileSync(file, 'utf8'))) {
      unenforced.push(`${route} — no noindex in its metadata, so it emits no robots meta`);
    }
  }

  // Every dynamic family must still point at a real resolver. Text, not an
  // import: these modules reach the server API client, and pulling that graph
  // into a build-time check is exactly what `policyModule` avoids.
  const rotted = [];
  for (const family of pages.DYNAMIC_ROUTE_FAMILIES) {
    let source;
    try {
      source = readFileSync(join(src, family.policyModule), 'utf8');
    } catch {
      rotted.push(`${family.pattern} — policyModule 'src/${family.policyModule}' does not exist`);
      continue;
    }
    if (family.policySymbol && !source.includes(family.policySymbol)) {
      rotted.push(
        `${family.pattern} — '${family.policySymbol}' is no longer in src/${family.policyModule}`,
      );
    }
  }

  const failures = [];

  if (rotted.length) {
    failures.push(
      `${rotted.length} dynamic route famil(ies) pointing at a resolver that moved:\n    ` +
        rotted.join('\n    ') +
        '\n  Update policyModule/policySymbol, or restore what they name.',
    );
  }

  if (undeclared.length) {
    failures.push(
      `${undeclared.length} route(s) with no declared indexation policy:\n    ` +
        undeclared.join('\n    ') +
        '\n  Declare each in exactly one of STATIC_PAGES, STATIC_NOINDEX_PAGES,' +
        '\n  REDIRECT_STUBS, DYNAMIC_ROUTE_FAMILIES (lib/pages.ts), or the' +
        '\n  robots.txt `*` group (app/robots.txt/route.ts).',
    );
  }

  if (doubleDeclared.length) {
    failures.push(
      `${doubleDeclared.length} route(s) declared in more than one bucket:\n    ` +
        doubleDeclared.join('\n    ') +
        '\n  seo-standard.md section 2: a disallowed page is never crawled, so a' +
        '\n  noindex on it is never read. Pick one.',
    );
  }

  if (unenforced.length) {
    failures.push(
      `${unenforced.length} noindex declaration(s) that are not true:\n    ` +
        unenforced.join('\n    ') +
        `\n  ${noindexFix}`,
    );
  }

  if (failures.length) {
    console.error('\ncheck-indexation-ledger failed:\n');
    for (const failure of failures) console.error(`• ${failure}\n`);
    process.exit(1);
  }

  console.log(
    `check-indexation-ledger: all ${routes.size} routes have exactly one true indexation policy.`,
  );
}
