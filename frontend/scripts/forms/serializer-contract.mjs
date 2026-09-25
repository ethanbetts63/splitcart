/**
 * Holds the login and signup forms to the DRF serializers they post to.
 *
 * ## The failure this exists to prevent
 *
 * A signup form that silently stops sending a field the backend requires. The
 * form still renders, the button still submits, and Django answers `400` with
 * `{"full_name": ["This field is required."]}` — for a field that is no longer
 * on the page. Nothing in the frontend can show that error, so the person sees
 * a button that appears to do nothing, over and over, with no way to act on it.
 * The mirror image is as quiet and costs as much: the form posts a key the
 * serializer never declared, DRF drops it on the floor, and the account is
 * created without it. That is exactly what happened to the anonymous cart —
 * registration took no `anonymous_id`, so a shopper who filled a cart signed
 * out lost it on signing up, while the same shopper signing *in* kept it.
 * `CustomRegisterSerializer` has since gained the field; this check is what
 * stops the two sides drifting apart again without anyone noticing.
 *
 * Typecheck cannot see any of this. The wire between a `FormData` and a DRF
 * serializer is untyped by construction, and the two halves are in different
 * languages in different halves of the repository.
 *
 * ## How both sides are read
 *
 * Neither side is scraped for its field list, because a regex over either one
 * fails the same way — matching nothing, silently, which is indistinguishable
 * from agreement.
 *
 *   - The **schema** is imported. `scripts/seo/ts-loader.mjs` lets a plain Node
 *     script `import()` a `.ts` module, so the field list is `schema.shape` —
 *     the real object, `.refine()` and all.
 *   - The **serializer** is imported too, by the repository's own interpreter:
 *     `venv/Scripts/python` under `settings_test`, printing `serializer().fields`
 *     as JSON. That is the only way to see fields the class *inherits* —
 *     `username` is declared by neither `CustomLoginSerializer` nor
 *     `CustomRegisterSerializer`, arrives from dj-rest-auth, and is a field the
 *     endpoint will accept. Reading the two `.py` files as text would miss it,
 *     and would miss a library upgrade changing whether it is required.
 *
 * Only the markup is read as text: `ts-loader` strips types but does not
 * transpile, so a `.tsx` cannot be imported at all.
 *
 * ## What it asserts
 *
 * 1. Every schema field has a control in the form that posts under that name,
 *    and every control's name is a schema field. A control deleted from the
 *    markup leaves a schema field nothing can ever fill.
 * 2. Every field the serializer *requires* is posted. No exception row can
 *    excuse this one.
 * 3. Every field the form posts is a field the serializer declares, and is not
 *    read-only. Anything else is a value the API silently discards.
 * 4. Every optional serializer field the form does not post carries a written
 *    reason, ledger-style. This is the rule with the teeth: `anonymous_id` was
 *    added to the register serializer as *optional*, and without this row a new
 *    optional field is precisely the kind of drift nothing else notices.
 *
 * What it cannot check is whether a posted value means the right thing — a
 * `full_name` holding an email address passes every rule here. That is review's
 * job, the same way FORMS-3 is.
 */
import { readFileSync, existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { registerTsLoader } from '../seo/ts-loader.mjs';

/**
 * Controls that post a value under their `name`. A control type missing from
 * this list makes its field look absent from the markup, which fails check 1
 * loudly rather than passing quietly — add the tag here when one appears.
 */
const CONTROL = /<(?:input|Input|textarea|Textarea|select|Select)\b[\s\S]*?\/>/g;
const NAME_ATTRIBUTE = /\bname="([^"]+)"/;

/**
 * Prints `{'<module>.<Class>': {field: {required, read_only}}}` for every
 * serializer named on argv. Run by the repository's own interpreter, so it is
 * the same import path `pytest` and `manage.py` take.
 */
const INTROSPECT = `
import importlib, json, sys
import django

django.setup()

fields = {}
for target in json.loads(sys.argv[1]):
    module, name = target.rsplit('.', 1)
    serializer = getattr(importlib.import_module(module), name)
    fields[target] = {
        field_name: {'required': field.required, 'read_only': field.read_only}
        for field_name, field in serializer().fields.items()
    }
print(json.dumps(fields))
`;

/** The venv this repository documents, by platform. */
function findInterpreter(repoRoot) {
  for (const relative of [
    join('venv', 'Scripts', 'python.exe'),
    join('venv', 'bin', 'python'),
    join('.venv', 'Scripts', 'python.exe'),
    join('.venv', 'bin', 'python'),
  ]) {
    const path = join(repoRoot, relative);
    if (existsSync(path)) return path;
  }
  return null;
}

/**
 * @param {string} repoRoot Absolute path to the repository root (Django's).
 * @param {string[]} targets `'<module>.<Class>'` for each serializer.
 */
function readSerializerFields(repoRoot, targets) {
  const python = findInterpreter(repoRoot);
  if (!python) {
    throw new Error(
      'no Python interpreter at venv/Scripts/python (or venv/bin/python).\n' +
        '  This check imports the DRF serializers rather than scraping them, so it\n' +
        '  needs the repository venv README.md describes:\n' +
        '      python -m venv venv\n' +
        '      .\\venv\\Scripts\\python.exe -m pip install -r requirements_dev.txt',
    );
  }

  const result = spawnSync(python, ['-c', INTROSPECT, JSON.stringify(targets)], {
    cwd: repoRoot,
    encoding: 'utf8',
    env: { ...process.env, DJANGO_SETTINGS_MODULE: 'settings_test', PYTHONIOENCODING: 'utf-8' },
  });

  if (result.status !== 0) {
    throw new Error(
      `${python} could not import the serializers (exit ${result.status}).\n` +
        `${(result.stderr || result.stdout || '').trim().replace(/^/gm, '      ')}`,
    );
  }

  // `settings_test` is the settings module the Python suite uses: `config.settings`
  // with SQLite substituted, so nothing here can reach for a MySQL grant that
  // does not exist. Django and allauth may write to stdout on the way up, so
  // the JSON is the last line, not the whole of it.
  const lines = result.stdout.trim().split(/\r?\n/);
  try {
    return JSON.parse(lines[lines.length - 1]);
  } catch {
    throw new Error(
      `${python} printed something other than JSON:\n${result.stdout.trim().replace(/^/gm, '      ')}`,
    );
  }
}

/** Every `name` a control in `source` posts under. */
function controlNames(source) {
  const names = new Set();
  for (const tag of source.match(CONTROL) ?? []) {
    const name = tag.match(NAME_ATTRIBUTE);
    if (name) names.add(name[1]);
  }
  return names;
}

/** The comparison itself, exit-free so it can be called without a process. */
export async function findContractProblems({ root, pairs }) {
  const source = join(root, 'src');
  const repoRoot = join(root, '..');
  registerTsLoader(source);

  const serializerFields = readSerializerFields(
    repoRoot,
    pairs.map((pair) => pair.serializer),
  );

  const problems = [];
  let posted = 0;

  for (const pair of pairs) {
    const { form, schema, serializer, endpoint } = pair;
    const shortSerializer = serializer.split('.').pop();
    const extras = pair.alsoPosts ?? [];
    const serverOnly = pair.serverOnly ?? [];

    const module = await import(pathToFileURL(join(source, ...schema.module.split('/'))).href);
    const zodSchema = module[schema.export];
    if (!zodSchema?.shape) {
      problems.push(
        `  ${schema.module}\n      exports no '${schema.export}' with a .shape — a z.object(), possibly\n      behind .refine(). Point the row at the schema this form parses with.`,
      );
      continue;
    }

    const schemaFields = Object.keys(zodSchema.shape);
    const formSource = readFileSync(join(source, ...form.split('/')), 'utf8');
    const markup = controlNames(formSource);
    const declared = serializerFields[serializer];
    const body = new Set([...schemaFields, ...extras.map((row) => row.field)]);
    posted += body.size;

    // 1. Schema and markup. A field nothing can fill, or a control nothing parses.
    for (const field of schemaFields) {
      if (!markup.has(field)) {
        problems.push(
          `  ${form}\n      form side: '${field}' is in ${schema.export} but no control posts under\n      that name. Nothing can ever fill it, so every submit fails validation\n      on a field the page does not show. Add the control, or drop the field\n      from the schema.`,
        );
      }
    }
    for (const field of markup) {
      if (!body.has(field)) {
        problems.push(
          `  ${form}\n      form side: a control posts '${field}', which ${schema.export} does not\n      declare. Add it to the schema, or to alsoPosts with the reason it is\n      not typed there.`,
        );
      }
    }

    // The extras are injected into the request body rather than typed, so the
    // only evidence they are still sent is the name appearing in the file that
    // assembles the body — the form itself, or the service module `in` names.
    for (const row of extras) {
      const bodyFile = row.in ?? form;
      const bodySource =
        bodyFile === form ? formSource : readFileSync(join(source, ...bodyFile.split('/')), 'utf8');
      if (!bodySource.includes(row.field)) {
        problems.push(
          `  ${form}\n      form side: the alsoPosts row for '${row.field}' is stale — the name\n      appears nowhere in ${bodyFile}, so the request body no longer carries\n      it. Restore it, or delete the row.`,
        );
      }
      if (markup.has(row.field)) {
        problems.push(
          `  ${form}\n      form side: '${row.field}' is an alsoPosts row but a control posts it.\n      A typed field belongs in ${schema.export}; alsoPosts is for values the\n      client supplies itself.`,
        );
      }
    }

    // 2 and 4. Every serializer field is posted, or excused in writing.
    const excused = new Map(serverOnly.map((row) => [row.field, row]));
    for (const [field, spec] of Object.entries(declared)) {
      if (spec.read_only || body.has(field)) continue;
      if (spec.required) {
        problems.push(
          `  ${form}\n      serializer side: ${shortSerializer} requires '${field}'.\n      This form never posts it, so ${endpoint}\n      answers 400 for a field the page cannot show an error against —\n      post it, or make the serializer field optional.`,
        );
      } else if (!excused.has(field)) {
        problems.push(
          `  ${form}\n      serializer side: ${shortSerializer} declares '${field}'.\n      This form does not post it. If that is deliberate, say so in a\n      serverOnly row; a new optional field nobody sends is how a feature\n      ships dead.`,
        );
      }
    }

    // 3. Every posted field is a field the endpoint will actually read.
    for (const field of body) {
      const spec = declared[field];
      if (!spec) {
        problems.push(
          `  ${form}\n      serializer side: this form posts '${field}', and\n      ${shortSerializer} declares no such field.\n      ${endpoint} discards it without a word — declare it on the\n      serializer, or stop sending it.`,
        );
      } else if (spec.read_only) {
        problems.push(
          `  ${form}\n      serializer side: this form posts '${field}', which\n      ${shortSerializer} declares read-only. DRF drops read-only fields\n      from input, so the value never reaches the model.`,
        );
      }
    }

    // Stale rows. An excuse outliving the field it excused is worse than none:
    // it reads as a decision somebody made about the shape the API has now.
    for (const row of serverOnly) {
      if (!declared[row.field]) {
        problems.push(
          `  ${form}\n      serverOnly names '${row.field}', which ${shortSerializer} no longer\n      declares. Delete the row.`,
        );
      } else if (body.has(row.field)) {
        problems.push(
          `  ${form}\n      serverOnly says '${row.field}' is not posted, but the form posts it.\n      Delete the row.`,
        );
      } else if (!String(row.why ?? '').trim()) {
        problems.push(
          `  ${form}\n      serverOnly row for '${row.field}' gives no reason. A field the server\n      accepts and the client never sends is a decision; write it down.`,
        );
      }
    }
  }

  return { problems, posted, pairCount: pairs.length };
}

export async function checkSerializerContract(options) {
  let result;
  try {
    result = await findContractProblems(options);
  } catch (error) {
    console.error(`\ncheck-form-contract could not run:\n\n  ${error.message}\n`);
    process.exit(1);
  }

  if (result.problems.length) {
    console.error('\ncheck-form-contract: a form and its serializer disagree.\n');
    console.error(result.problems.join('\n'));
    console.error(
      '\nThe form half is frontend/src; the serializer half is users/serializers.\n' +
        'The pairs and their exception rows are scripts/check-form-contract.mjs.\n',
    );
    process.exit(1);
  }

  console.log(
    `check-form-contract: ${result.pairCount} form/serializer pairs agree on ` +
      `all ${result.posted} posted fields.`,
  );
}
