/**
 * Every form in the app is on a track, or is excluded with a written reason.
 *
 * Shared engine — edit it in `freetheplatform/frontend/registry/tooling/forms/`
 * and re-sync, never in a product. The ledger it checks is repo-specific and is
 * the whole point: adding a row is where somebody has to say, in words, which
 * track a new form is on or why it is not a form.
 *
 * Why a ledger and not a sniffer. The obvious check — find `<form>`, look for
 * `useActionState` or `zodResolver` beside it — is wrong in both directions.
 * A Track B form's schema and action live in sibling files, not in the
 * component. A shared wrapper can own the `<form>` for a panel whose rules live
 * somewhere else entirely, so the file with the markup has no track and the
 * file with the track has no markup. And a configurator preview that renders a
 * mocked customer site has a `<form>` that submits nowhere. None of those can
 * be told apart by reading one file; all of them can be written down once.
 *
 * So this checks the thing a script can actually check: that the ledger and the
 * tree agree. A new form is a new row. A deleted form is a deleted row. What it
 * cannot check is whether a row is honest — that is what review is for, and
 * why every excluded row carries its reason in the same table.
 *
 * With `requireErrorSummary` (a repo opts in, FORMS-12), every A or B form must
 * render `FormErrorSummary` or carry a `summary` reason saying why it needs
 * none, such as a two-field form whose error already sits by its button. A
 * reason on a form that does render one is stale and is reported too.
 *
 * See freetheplatform/_docs/forms-standard.md.
 */
import { readFileSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { walk } from './walk.mjs';

/** A `<form` opening tag, not the word "form" in prose or a className. */
const FORM_TAG = /<form[\s>]/;

/** The shared error-summary component, by name, in the form's own file. */
const ERROR_SUMMARY = /\bFormErrorSummary\b/;

/** The comparison itself, exit-free so the test suite can call it. */
export function findFormLedgerProblems({ root, ledger, requireErrorSummary = false }) {
  const source = join(root, 'src');
  const found = new Map();
  for (const path of walk(source, ['.tsx'])) {
    const text = readFileSync(path, 'utf8');
    if (FORM_TAG.test(text)) {
      found.set(relative(source, path).split(sep).join('/'), text);
    }
  }

  const listed = new Map(ledger.map((row) => [row.file, row]));
  const problems = [];

  for (const file of [...found.keys()].sort()) {
    if (!listed.has(file)) {
      problems.push(
        `  ${file}\n      renders a <form> and is not in the ledger. Add a row saying which\n      track it is on, or why neither applies.`,
      );
    }
  }
  for (const row of ledger) {
    if (!found.has(row.file)) {
      problems.push(
        `  ${row.file}\n      is in the ledger but renders no <form>. Remove the row, or point it\n      at the file that does.`,
      );
    }
    if (row.track !== 'A' && row.track !== 'B' && !String(row.why ?? '').trim()) {
      problems.push(
        `  ${row.file}
      is '${row.track}' with no reason given. A row that is not on a track
      says why in words: what excludes it, who owns it, or what is left.`,
      );
    }
    if (requireErrorSummary && (row.track === 'A' || row.track === 'B') && found.has(row.file)) {
      const renders = ERROR_SUMMARY.test(found.get(row.file));
      const reason = String(row.summary ?? '').trim();
      if (!renders && !reason) {
        problems.push(
          `  ${row.file}
      renders no FormErrorSummary. List a failed submit's problems at the top
      of the form with it, or give the row a \`summary\` saying why this form
      needs none (FORMS-12).`,
        );
      }
      if (renders && reason) {
        problems.push(
          `  ${row.file}
      renders FormErrorSummary but its row still says it needs none. Drop the
      \`summary\` reason.`,
        );
      }
    }
  }

  return { problems, formCount: found.size };
}

export function checkFormLedger({ root, ledger, requireErrorSummary = false }) {
  const { problems, formCount } = findFormLedgerProblems({ root, ledger, requireErrorSummary });

  if (problems.length) {
    console.error('check-forms: the ledger and the tree disagree.\n');
    console.error(problems.join('\n'));
    console.error(
      '\nThe ledger is this file. The rules are\n' + 'freetheplatform/_docs/forms-standard.md.',
    );
    process.exit(1);
  }

  const counts = ledger.reduce((totals, row) => {
    totals[row.track] = (totals[row.track] ?? 0) + 1;
    return totals;
  }, {});
  const summary = Object.entries(counts)
    .sort()
    .map(([track, count]) => `${count} ${track}`)
    .join(', ');
  console.log(
    `check-forms: all ${formCount} files rendering a <form> are accounted for (${summary}).`,
  );
}
