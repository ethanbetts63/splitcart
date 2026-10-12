/**
 * The parts of the forms standard a script can hold, beyond the ledger. Shared engine: edit it in
 * `freetheplatform/frontend/registry/tooling/forms/` and re-sync. Repo-specific facts (session cookies, files
 * allowed to read the Django base URL) come from each repo's `scripts/check-forms.mjs`; an exception is a row with a reason.
 *
 * 1. Form schemas live in `*.schema.ts`; a `z.object(` elsewhere goes in `schemaExceptions` with its reason.
 * 2. Every `z.string(` chain in a `*.schema.ts` carries `.max(`, and a raw ceiling never exceeds 255 (`FIELD_MAX.line`);
 *    wider is a field kind taken from `FIELD_MAX`, so frontend and serializer bound the same field.
 * 3. `DJANGO_API_URL` is read only by the files that own it, or an app ends up half on `localhost` (may resolve IPv6-first) and half on `127.0.0.1`.
 * 4. Only the local wrapper imports the package `serverApiFetch` (by name or namespace), and its `forwardCookies` is
 *    exactly the session cookies, with no second allowlist: a Server Action reads the whole jar, so without it
 *    analytics, consent and capability cookies would go to Django.
 *
 * These catch honest mistakes, not adversaries. Whether ceilings use the right kinds or a track was chosen correctly
 * is review's job (FORMS-3).
 */
import { readFileSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { walk } from './walk.mjs';

/** Every `z.string(...)` call with its full method chain, found by balanced parentheses so a prettier-wrapped chain is one chain. Exported for tests. */
export function stringChains(text) {
  const chains = [];
  // `\s*` around the dot: prettier can wrap at `.string()`, and skipping such a chain would hide an unbounded field.
  const opener = /\bz\s*\.\s*string\s*\(/g;
  let match;
  while ((match = opener.exec(text)) !== null) {
    let i = match.index + match[0].length - 1; // at the '('
    let depth = 0;
    do {
      if (text[i] === '(') depth += 1;
      else if (text[i] === ')') depth -= 1;
      i += 1;
    } while (depth > 0 && i < text.length);
    // Consume `.method(...)` links while they follow.
    for (;;) {
      let j = i;
      while (/\s/.test(text[j])) j += 1;
      if (text[j] !== '.') break;
      j += 1;
      while (/[\w$]/.test(text[j])) j += 1;
      while (/\s/.test(text[j])) j += 1;
      if (text[j] !== '(') break;
      depth = 0;
      do {
        if (text[j] === '(') depth += 1;
        else if (text[j] === ')') depth -= 1;
        j += 1;
      } while (depth > 0 && j < text.length);
      i = j;
    }
    chains.push({
      line: text.slice(0, match.index).split('\n').length,
      chain: text.slice(match.index, i),
    });
  }
  return chains;
}

const WIDEST_RAW_CEILING = 255; // FIELD_MAX.line

/** The checks themselves, exit-free so the test suite can call them. */
export function findFormHygieneProblems({
  root,
  sessionCookies,
  wrapperFile = 'lib/serverApi.ts',
  envReaders = [],
  schemaExceptions = [],
}) {
  const source = join(root, 'src');
  const problems = [];
  const posix = (path) => relative(source, path).split(sep).join('/');

  let schemaFiles = 0;
  const envAllowed = new Map(envReaders.map((row) => [row.file, row]));
  const schemaAllowed = new Map(schemaExceptions.map((row) => [row.file, row]));
  for (const row of [...envReaders, ...schemaExceptions]) {
    if (!String(row.why ?? '').trim()) {
      problems.push(
        `  ${row.file}\n      is listed as an exception with no reason given. Say why.`,
      );
    }
  }

  for (const path of walk(source, ['.ts', '.tsx'])) {
    const file = posix(path);
    const text = readFileSync(path, 'utf8');
    const isSchema = file.endsWith('.schema.ts');

    if (isSchema) {
      schemaFiles += 1;
      for (const { line, chain } of stringChains(text)) {
        const ceiling = chain.match(/\.max\(\s*([^),]*)/);
        if (!ceiling) {
          problems.push(
            `  ${file}:${line}\n      z.string() with no .max(). Every string field carries a ceiling —\n      use a FIELD_MAX kind (forms-standard.md, FORMS-6).`,
          );
        } else if (/^\d+$/.test(ceiling[1].trim()) && Number(ceiling[1]) > WIDEST_RAW_CEILING) {
          problems.push(
            `  ${file}:${line}\n      .max(${ceiling[1].trim()}) is a raw number wider than FIELD_MAX.line (255).\n      A ceiling that big is a field kind — take it from FIELD_MAX so the\n      serializer side bounds the same field.`,
          );
        }
      }
    } else if (/\bz\.object\(/.test(text) && !schemaAllowed.has(file)) {
      problems.push(
        `  ${file}\n      builds a z.object() outside a *.schema.ts file. A form schema lives\n      in its own schema file beside the form; if this is not a form,\n      add it to schemaExceptions with the reason.`,
      );
    }

    if (/\bDJANGO_API_URL\b/.test(text) && !envAllowed.has(file)) {
      problems.push(
        `  ${file}\n      reads DJANGO_API_URL inline. The base URL and its fallback are owned\n      by ${envReaders.map((row) => row.file).join(', ') || 'one lib module'} —\n      import the constant instead, or add an envReaders row saying why not.`,
      );
    }

    if (file !== wrapperFile) {
      const imports = text.matchAll(
        /import\s+(?:type\s+)?{([^}]*)}\s*from\s*['"]@freetheplatform\/web-security['"]/g,
      );
      for (const found of imports) {
        if (/\bserverApiFetch\b/.test(found[1])) {
          problems.push(
            `  ${file}\n      imports serverApiFetch from the package directly. Only ${wrapperFile}\n      does that — it is where the cookie allowlist lives. Import the local\n      wrapper instead.`,
          );
        }
      }
      if (/import\s*\*\s*as\s+[\w$]+\s+from\s*['"]@freetheplatform\/web-security['"]/.test(text)) {
        problems.push(
          `  ${file}\n      namespace-imports @freetheplatform/web-security, which hides whether\n      serverApiFetch is reached. Import the names this file uses.`,
        );
      }
    }
  }

  const wrapper = readFileSync(join(source, ...wrapperFile.split('/')), 'utf8');
  const declared = wrapper.match(/const SESSION_COOKIES\s*=\s*\[([^\]]*)\]/);
  const literals = declared ? [...declared[1].matchAll(/'([^']*)'|"([^"]*)"/g)] : [];
  const cookies = literals.map((m) => m[1] ?? m[2]);
  if (!declared || !/forwardCookies:\s*SESSION_COOKIES\b/.test(wrapper)) {
    problems.push(
      `  ${wrapperFile}\n      must pass forwardCookies: SESSION_COOKIES, with SESSION_COOKIES a\n      literal array. Name the cookies; never forward the jar.`,
    );
  } else if (
    cookies.length !== sessionCookies.length ||
    sessionCookies.some((name) => !cookies.includes(name))
  ) {
    problems.push(
      `  ${wrapperFile}\n      forwards [${cookies.join(', ')}] but the session cookies are\n      [${sessionCookies.join(', ')}]. Django reads nothing else — every extra\n      name here is a cookie leaked to it on every authenticated action.`,
    );
  }
  // One allowlist: a second forwardCookies (a spread, a wider literal) passes the checks above while forwarding more than the session.
  const rogue = [...wrapper.matchAll(/forwardCookies\s*:\s*([^,}\r\n]+)/g)]
    .map((m) => m[1].trim())
    .filter((value) => value !== 'SESSION_COOKIES');
  if (rogue.length) {
    problems.push(
      `  ${wrapperFile}\n      passes forwardCookies with something other than the SESSION_COOKIES\n      identifier: ${rogue.join('; ')}. One allowlist — extend SESSION_COOKIES\n      or change the standard, never a second list.`,
    );
  }

  return { problems, schemaFiles };
}

export function checkFormHygiene(options) {
  const { problems, schemaFiles } = findFormHygieneProblems(options);

  if (problems.length) {
    console.error('check-forms: hygiene problems.\n');
    console.error(problems.join('\n'));
    console.error('\nThe rules are freetheplatform/_docs/forms-standard.md.');
    process.exit(1);
  }

  console.log(
    `check-forms: ${schemaFiles} schema files bounded; DJANGO_API_URL confined to ` +
      `${options.envReaders?.length ?? 0} file(s); forwarding only [${options.sessionCookies.join(', ')}].`,
  );
}
