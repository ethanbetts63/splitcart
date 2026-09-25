/**
 * Fails the build when an image path the SEO modules name does not exist.
 *
 * Adapted from `freethedesk/frontend/scripts/seo/og-images.mjs`. SplitCart is
 * not a component-registry consumer yet (see `_docs/convergence/registry.md`),
 * so this is a local copy rather than a synced one. Two deliberate local
 * changes, both marked below: the literal pattern accepts double quotes,
 * because this repo's TypeScript is double-quoted throughout; and it accepts
 * `.ico`, because the manifest names one.
 *
 * A missing OG image is invisible until somebody shares the link and gets a
 * bare URL instead of a preview card. SplitCart shipped exactly that:
 * `defaultOgImage` pointed at `/static/square-image.jpg`, `createMetadata()`
 * puts it on every page, and `public/` had no `/static/` directory at all — so
 * every social share of every URL on the site linked a 404. See
 * seo-standard.md section 4 (SEO-4).
 *
 * Only `public/`-relative paths are checked. An absolute URL belongs to someone
 * else, and an imported asset resolves to a hashed `/_next/` URL that exists by
 * construction.
 *
 * This scans source TEXT rather than importing values, deliberately: it is a
 * superset scan with no idea which field it is looking at, which is the point —
 * an image path is worth validating wherever it appears, including inside a
 * function body no export exposes. The pattern is anchored at both ends on
 * `'/….ext'`, so prose cannot accidentally look like one, and a quoting style
 * it misses costs a skipped check rather than a wrong answer.
 */
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

// Local change vs. the freethedesk original: `["']` rather than `'`, and `ico`
// in the extension set.
const IMAGE_LITERAL = /["'](\/[^"']*\.(?:webp|png|jpe?g|svg|avif|gif|ico))["']/g;

/**
 * @param {object} options
 * @param {string} options.root      Absolute path to the repo's `frontend`.
 * @param {string[]} options.sources Repo-relative files to scan.
 */
export function checkOgImages({ root, sources }) {
  const publicDir = join(root, 'public');
  const referenced = new Set();

  for (const relative of sources) {
    const source = readFileSync(join(root, relative), 'utf8');
    for (const match of source.matchAll(IMAGE_LITERAL)) referenced.add(match[1]);
  }

  const missing = [...referenced].filter((path) => !existsSync(join(publicDir, path)));

  if (missing.length) {
    console.error('\ncheck-og-images failed:\n');
    console.error(`• ${missing.length} image path(s) named in the SEO modules do not exist:`);
    for (const path of missing) console.error(`    public${path}`);
    console.error(
      '\n  Make the file, or drop the field so the page falls back to the' +
        '\n  default OG image.\n',
    );
    process.exit(1);
  }

  console.log(`check-og-images: all ${referenced.size} referenced image paths exist.`);
}
