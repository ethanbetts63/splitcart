#!/usr/bin/env node
/**
 * Fails the build when the design-token declarations drift apart.
 *
 * The invariants and the reasons for them live in freetheplatform's shared
 * lint directory, beside the ESLint and Stylelint configs that enforce the
 * same token contract (LINT-10). This file says where splitcart keeps its
 * files, and adds one invariant the shared module does not carry yet -- see
 * `danglingInMarkup` below.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { tokenDrift } from '../../../freetheplatform/frontend/lint/token-drift.mjs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');

/**
 * Every var(--x) an arbitrary Tailwind value reads must be declared somewhere.
 *
 * This is invariant 4 of the shared module, aimed at the other half of the
 * codebase. Upstream scans stylesheets, because in allbikes and freethedesk
 * that is where a retired token is left behind. splitcart's presentation is in
 * class strings, and its dangling reads were there: `FaqSection.tsx` asked for
 * `--text-light-primary`, `--bg-light-primary`, `--text-dark-primary` and
 * `--text-dark-secondary`, none of which had ever been declared in this repo.
 * An unresolvable var() does not mean "ignore the var", it means "this
 * declaration is invalid", so five headings and paragraphs rendered with no
 * colour of their own and CSS reported nothing. The same shape caught
 * `sonner.tsx` reading `--radius` after the radius ramp was named by rung.
 *
 * It belongs upstream in token-drift.mjs once the other repos want it; it is
 * here rather than copied from there because there is nothing there to copy.
 *
 * A var() with a fallback is a deliberate optional override and is skipped,
 * matching upstream. So is a name the markup itself sets through a style prop,
 * and so is anything in EXTERNAL.
 */

/**
 * Custom properties something other than this repo declares, at runtime.
 * Each entry needs a reason; "the check was noisy" is not one.
 */
const EXTERNAL = [
  // Radix measures a trigger or a viewport and writes its size onto the
  // element as a custom property just before the content paints.
  /^--radix-/,
  // Tailwind v4's own theme variable behind the numeric spacing scale, which
  // `alert.tsx` reads to size a grid column to `size-4`.
  /^--spacing$/,
];

/** Comments name tokens without reading them; a rename must not trip on prose. */
const stripComments = (source) =>
  source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^[ \t]*\/\/.*$/gm, '');

function danglingInMarkup() {
  // A filesystem walk rather than `git ls-files`, because the token file is
  // itself new in the commit that adds this check and git does not know it yet.
  const walk = (dir, ext, out = []) => {
    for (const entry of readdirSync(join(root, dir), { withFileTypes: true })) {
      const path = `${dir}/${entry.name}`;
      if (entry.isDirectory()) walk(path, ext, out);
      else if (entry.name.endsWith(ext)) out.push(path);
    }
    return out;
  };

  const declared = new Set();
  for (const file of walk('src', '.css')) {
    for (const m of stripComments(readFileSync(join(root, file), 'utf8')).matchAll(
      /(--[a-z0-9-]+)\s*:/g,
    )) {
      declared.add(m[1]);
    }
  }

  const markup = walk('src', '.tsx').map((file) => [
    file,
    stripComments(readFileSync(join(root, file), 'utf8')),
  ]);
  // `style={{ '--x': ... }}` declares a token for its own subtree.
  for (const [, source] of markup) {
    for (const m of source.matchAll(/['"](--[a-z0-9-]+)['"]\s*:/g)) declared.add(m[1]);
  }

  const dangling = [];
  for (const [file, source] of markup) {
    for (const m of source.matchAll(/var\(\s*(--[a-z0-9-]+)\s*([,)])/g)) {
      if (m[2] === ',') continue;
      if (declared.has(m[1]) || EXTERNAL.some((p) => p.test(m[1]))) continue;
      dangling.push(`${file}: ${m[1]}`);
    }
  }
  if (!dangling.length) return [];
  return [
    `These components read a design token that is not declared anywhere, so the\n` +
      `  whole declaration is invalid and the element inherits instead:\n    ` +
      `${[...new Set(dangling)].join('\n    ')}\n` +
      `  Point them at the token that replaced it, or declare it in tokens.css.`,
  ];
}

const { failures } = tokenDrift({ root, tokensPath: 'src/styles/tokens.css' });
failures.push(...danglingInMarkup());

if (failures.length) {
  console.error('\ncheck-tokens failed:\n');
  for (const f of failures) console.error(`• ${f}\n`);
  process.exit(1);
}
console.log('check-tokens: token declarations agree.');
