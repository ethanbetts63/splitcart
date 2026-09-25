/**
 * Maximum lengths, declared per field *kind* rather than per field.
 *
 * A browser-side maximum constrains nothing on its own. This exists so the
 * person typing is told at the point of typing, and so the schema stops a
 * paste before it becomes a request — the serializer stops everything else,
 * including a caller who never loaded the page. That only works if both ends
 * bound the same field to the same number.
 *
 * ## Why this table is here rather than imported
 *
 * The canonical pair is `freetheplatform.security.bounds` and
 * `@freetheplatform/web-security`, held equal by a test in that package's own
 * suite (FORMS-8). splitcart installs neither, and `AGENTS.md` says adding one
 * is a decision that applies `strategy.md`'s tests first — a larger question
 * than bounding three forms. So this is a *mirror*, copied kind for kind and
 * value for value, and `users/serializers/bounds.py` is the same mirror on the
 * Django side. `users/tests/serializer_tests/test_bounds.py` pins both against
 * one literal table, this file included, so neither can drift on its own.
 *
 * What no test in this repository can see is the *shared* table changing. That
 * is the part the conformance ledger records as `n/a` rather than as a pass,
 * and it closes the day splitcart depends on the package: delete this file,
 * import `FIELD_MAX` from `@freetheplatform/web-security`, and the names are
 * deliberately identical so that is the whole change.
 *
 * See `../../../freetheplatform/_docs/forms-standard.md`.
 */
import { z } from 'zod';

export const FIELD_MAX = {
  // Identity and contact.
  name: 120,
  business_name: 180,
  // 150, not the 254 that SMTP allows, because an address here becomes an
  // account and Django's `auth.User.username` column is 150 characters. Two
  // addresses agreeing on their first 150 characters would collide on a unique
  // constraint and the second person would be told they already have an
  // account, with no way forward.
  email: 150,
  phone: 40,
  // Django stores its hashes in a 128-character column and bounds its own
  // password inputs the same way. The bound is not about password strength; it
  // is about how much data the hasher is asked to chew through.
  password: 128,
  // Short structured strings.
  slug: 120,
  // An identifier minted somewhere else: a plate, a VIN, an order reference.
  reference: 64,
  // A short machine-shaped string whose meaning its own validation supplies: a
  // price or a time typed into a form, a year, an id chosen from a select.
  token: 32,
  postcode: 16,
  // Free text, by how much of it a human is expected to write.
  /** One line: an address line, a subject, a label, a cart's name. */
  line: 255,
  // Django's `URLField` is 200 characters unless told otherwise. A bound wider
  // than the column is not a looser rule, it is a failed write.
  url: 200,
  /** A paragraph typed by a customer into a public form. */
  note: 2000,
  /** Body copy written by staff: a product description, an article. */
  long_text: 20_000,
  /** A stored rich-text document. */
  html: 200_000,
} as const;

export type FieldKind = keyof typeof FIELD_MAX;

function tooLong(kind: FieldKind): string {
  return `Keep this to ${FIELD_MAX[kind]} characters or fewer.`;
}

/**
 * A bounded string that must not be blank.
 *
 * Trimmed before it is measured: a field holding only whitespace is empty, and
 * a maximum applied to the untrimmed value silently allows a longer one.
 */
export function requiredString(kind: FieldKind, message = 'This field is required.') {
  return z.string().trim().max(FIELD_MAX[kind], tooLong(kind)).min(1, message);
}

/**
 * An email address: bounded, then format-checked.
 *
 * Bounded as well as checked because Zod's email test accepts an arbitrarily
 * long local part, and an address that cannot be delivered is not one worth
 * storing.
 */
export function email(required = 'Enter your email address.') {
  return z
    .string()
    .trim()
    .max(FIELD_MAX.email, tooLong('email'))
    .min(1, required)
    .pipe(z.email('Enter a valid email address.'));
}

/**
 * A password, bounded at the top by what the hasher should be asked to do.
 *
 * `minimum` is Django's `MinimumLengthValidator` restated; the server is still
 * the thing that enforces it, and this only saves a round trip. A field for an
 * *existing* credential passes `0` — a minimum there would reject a password
 * that predates the current rule instead of letting the server say so.
 */
export function password(minimum = 8) {
  const base = z.string().max(FIELD_MAX.password, tooLong('password'));
  return minimum > 0
    ? base.min(minimum, `Use at least ${minimum} characters.`)
    : base.min(1, 'Enter your password.');
}
