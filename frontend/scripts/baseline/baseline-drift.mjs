#!/usr/bin/env node
/**
 * The frontend baseline, held by a script instead of a table in a document.
 *
 * Shared engine — edit it in `freetheplatform/frontend/registry/tooling/` and
 * re-sync, never in a product. It is deliberately self-contained: the pinned
 * list is family policy, not a repo fact, so changing it is a registry edit
 * that lands everywhere in one sync.
 *
 * frontend-baseline.md's rule is that the products run one baseline —
 * the registry ships components by byte-copy, so a version skew means the
 * copy is not the thing that was tested. This script holds the part of that
 * rule that is already true:
 *
 * - PINNED packages must be declared identically in every repo a row names.
 *   Fail.
 * - BASELINE packages should be, but the family has not leveled them yet —
 *   the sequence is in _docs/frontend-baseline-outstanding.md. Warn, count.
 *   When a leveling step lands, move its packages into PINNED in the same
 *   change; that is the step becoming permanent.
 *
 * Run from any repo in the family. When the sibling repos are not present
 * (Vercel, CI, a lone clone) there is nothing to compare, so it says so and
 * exits 0 — the check is about the family, and only means something where
 * the family is.
 *
 *   node scripts/baseline/baseline-drift.mjs            enforce
 *   node scripts/baseline/baseline-drift.mjs --report   full table of skews
 */
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const CONSUMERS = ['allbikes', 'bloomprint', 'freethedesk', 'splitcart'];

/**
 * Declared identically today. Drifting one of these is a failure.
 *
 * A row is a package name (expected in every repo), or `{ name, repos }` for a
 * dependency only some of the family shares. Before scoped rows existed a
 * two-repo package was structurally invisible here — which is how lucide-react
 * sat a major version apart between allbikes and bloomprint for a while
 * (BASE-4). A scoped package appearing in a repo outside its row is also a
 * failure: that is the row gone stale, so widen it.
 */
const PINNED = [
  '@vercel/analytics',
  'class-variance-authority',
  'clsx',
  'stylelint',
  'stylelint-config-standard',
  'stylelint-declaration-strict-value',
  'typescript',
  // Two packages every founding repo has and splitcart does not yet. Scoped
  // rather than widened so the check stays meaningful in all four repos: a
  // bare row would fail everywhere for a gap splitcart is scheduled to close,
  // and a permanently red check is a check nobody reads. The stray detection
  // below is what closes the loop — the day splitcart declares either one, the
  // row goes stale loudly and gets widened.
  //   @freetheplatform/web-security — splitcart/_docs/convergence/auth-migration.md
  //   zod                           — splitcart/_docs/convergence/forms.md
  { name: '@freetheplatform/web-security', repos: ['allbikes', 'bloomprint', 'freethedesk'] },
  { name: 'zod', repos: ['allbikes', 'bloomprint', 'freethedesk'] },
  { name: 'lucide-react', repos: ['allbikes', 'bloomprint', 'splitcart'] },
  { name: 'marked', repos: ['allbikes', 'freethedesk'] },
  { name: 'tw-animate-css', repos: ['allbikes', 'bloomprint', 'splitcart'] },
  { name: 'sonner', repos: ['bloomprint', 'splitcart'] },
  // The Radix primitives more than one repo builds on. Before splitcart joined
  // these were a two-repo dependency with no row at all — structurally the
  // same blind spot that let lucide-react drift a major version (BASE-4).
  // They carry the family's caret, not an exact pin: BASE-5 wants exact, but
  // BASE-1 wants identical, and levelling a caret to a pin is a family-wide
  // change (BASE-2) rather than something a single repo joining can do.
  { name: '@radix-ui/react-checkbox', repos: ['allbikes', 'bloomprint', 'splitcart'] },
  { name: '@radix-ui/react-dialog', repos: ['allbikes', 'splitcart'] },
  { name: '@radix-ui/react-label', repos: ['allbikes', 'bloomprint', 'splitcart'] },
  { name: '@radix-ui/react-select', repos: ['allbikes', 'bloomprint', 'splitcart'] },
  { name: '@radix-ui/react-slider', repos: ['bloomprint', 'splitcart'] },
  { name: '@radix-ui/react-slot', repos: ['allbikes', 'bloomprint', 'splitcart'] },
  { name: '@radix-ui/react-switch', repos: ['allbikes', 'splitcart'] },
];

/**
 * The rest of the baseline: not yet leveled. Warned about, never silently
 * fine. The leveling order and its risk notes are
 * freetheplatform/_docs/frontend-baseline-outstanding.md.
 */
const BASELINE = [
  '@hookform/resolvers',
  '@stripe/react-stripe-js',
  '@stripe/stripe-js',
  '@tailwindcss/postcss',
  '@types/node',
  '@types/react',
  '@types/react-dom',
  'eslint',
  'eslint-config-next',
  'isomorphic-dompurify',
  'next',
  'prettier',
  'react',
  'react-dom',
  'react-hook-form',
  'tailwind-merge',
  'tailwindcss',
];

// Walk up from this file to the directory that holds the family checkout.
let workspace = dirname(fileURLToPath(import.meta.url));
while (
  workspace !== dirname(workspace) &&
  !CONSUMERS.every((repo) => existsSync(join(workspace, repo)))
) {
  workspace = dirname(workspace);
}

const present = CONSUMERS.filter((repo) =>
  existsSync(join(workspace, repo, 'frontend', 'package.json')),
);
if (present.length < CONSUMERS.length) {
  console.log(
    `baseline-drift: family checkout not present (found ${present.length}/${CONSUMERS.length} repos) — nothing to compare here.`,
  );
  process.exit(0);
}

const declared = new Map(
  CONSUMERS.map((repo) => {
    const manifest = JSON.parse(
      readFileSync(join(workspace, repo, 'frontend', 'package.json'), 'utf8'),
    );
    return [repo, { ...manifest.dependencies, ...manifest.devDependencies }];
  }),
);

const rowsOf = (list) =>
  list.map((entry) => (typeof entry === 'string' ? { name: entry, repos: CONSUMERS } : entry));

const versionsOf = (name, repos = CONSUMERS) =>
  repos.map((repo) => declared.get(repo)[name] ?? '—');
const agrees = (versions) => new Set(versions).size === 1 && !versions.includes('—');
/** A scoped row's package declared by a repo the row does not name. */
const straysOf = ({ name, repos }) =>
  CONSUMERS.filter((repo) => !repos.includes(repo) && name in declared.get(repo));

if (process.argv.includes('--report')) {
  const pinnedRows = rowsOf(PINNED);
  const scoped = new Map(
    pinnedRows.filter((row) => row.repos !== CONSUMERS).map((r) => [r.name, r]),
  );
  const pinnedNames = new Set(pinnedRows.map((row) => row.name));
  const shared = [...new Set(CONSUMERS.flatMap((repo) => Object.keys(declared.get(repo))))]
    .filter((name) => scoped.has(name) || CONSUMERS.every((repo) => name in declared.get(repo)))
    .sort();
  console.log(`baseline-drift: ${resolve(workspace)}\n`);
  console.log(['package'.padEnd(36), ...CONSUMERS.map((repo) => repo.padEnd(14))].join(''));
  for (const name of shared) {
    const versions = versionsOf(name);
    const row = scoped.get(name);
    const mark = pinnedNames.has(name) ? 'pin ' : BASELINE.includes(name) ? 'base' : '    ';
    const ok = row
      ? agrees(versionsOf(name, row.repos)) && !straysOf(row).length
      : agrees(versions);
    console.log(
      [`${ok ? ' ' : '!'} ${mark} ${name}`.padEnd(42), ...versions.map((v) => v.padEnd(14))].join(
        '',
      ),
    );
  }
  process.exit(0);
}

const failures = rowsOf(PINNED)
  .map((row) => ({ ...row, versions: versionsOf(row.name, row.repos), strays: straysOf(row) }))
  .filter(({ versions, strays }) => !agrees(versions) || strays.length);
const drifting = rowsOf(BASELINE)
  .map(({ name, repos }) => versionsOf(name, repos))
  .filter((versions) => !agrees(versions));

if (failures.length) {
  console.error('baseline-drift: pinned packages disagree.\n');
  for (const { name, repos, versions, strays } of failures) {
    console.error(`  ${name}`);
    repos.forEach((repo, i) => console.error(`      ${repo.padEnd(12)} ${versions[i]}`));
    for (const repo of strays) {
      console.error(
        `      ${repo.padEnd(12)} ${declared.get(repo)[name]}  (outside this row's repos — widen the row)`,
      );
    }
  }
  console.error(
    '\nThe rule is one baseline (freetheplatform/_docs/frontend-baseline.md).\n' +
      'Level these in every repo in one change — or, if the family is moving\n' +
      'together, finish the move.',
  );
  process.exit(1);
}

console.log(
  `baseline-drift: ${PINNED.length} pinned packages agree across ${CONSUMERS.length} repos` +
    (drifting.length
      ? `; ${drifting.length} baseline packages still drift (run with --report; the sequence is _docs/frontend-baseline-outstanding.md).`
      : '; the whole baseline agrees.'),
);
