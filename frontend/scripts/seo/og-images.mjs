/**
 * Fails the build when a page's OG image does not exist: a missing one is invisible until someone shares the link
 * and gets a bare URL. Validate at the write site (seo-standard.md section 4), not by rerouting missing images to the default.
 *
 * Only `public/`-relative paths are checked; an imported asset's `.src` is hashed under `/_next/` and an absolute URL is not ours.
 *
 * Unlike the other two checks this scans source text, deliberately: an image path is worth validating wherever it appears,
 * including inside a function body no export exposes. The pattern is anchored at both ends on a quoted `'/….ext'` or
 * `"/….ext"` (splitcart's TypeScript is double-quoted), so prose cannot match, and a quoting style it misses skips a check
 * rather than giving a wrong answer. `.ico` is an image too: a manifest names one.
 */
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

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
      '\n  Make the file, point at an imported asset (`someImage.src`), or drop the' +
        '\n  field so the page falls back to the default OG image.\n',
    );
    process.exit(1);
  }

  console.log(`check-og-images: all ${referenced.size} referenced image paths exist.`);
}
