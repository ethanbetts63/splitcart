# Convergence plan — forms

**Type:** status and work plan. Non-normative. The binding rules are
[`forms-standard.md`](../../../freetheplatform/_docs/forms-standard.md)
(FORMS-1..11).

Evidence: `scratchpad/gap-forms.md` (survey of 2026-09-25).

## The inventory

The survey searched exhaustively. splitcart has far fewer forms than its
component names suggest — most of the obvious candidates turn out not to be
forms at all.

| File                                            | Renders `<form>` | Submits to                          | Track                                           | Validation today                     |
| ----------------------------------------------- | ---------------- | ----------------------------------- | ----------------------------------------------- | ------------------------------------ |
| `components/ui/login-form.tsx`                  | yes              | `POST /api/auth/login/`             | B                                               | none — HTML `required` only          |
| `components/ui/signup-form.tsx`                  | yes              | `POST /api/auth/registration/`      | B — confirm-password is not a cross-field rule under the standard's own carve-out | manual password-match check          |
| `page_components/dialog-pages/CartPage.tsx`     | **no**           | `POST /api/carts/rename/`           | B, once it has a `<form>`                       | none, client or server               |
| `components/NavSearchBar.tsx`                   | no               | client-side navigation only         | excluded — no network write                     | n/a                                  |
| `components/settings-dialog.tsx`                | no               | nothing                             | not a form                                      | n/a                                  |
| `page_components/ContactPage.tsx`, `ContactDetails.tsx` | no       | nothing — static copy, email in prose | **there is no contact form in this app**        | n/a                                  |
| `page_components/FinalCartPage.tsx` buttons     | no               | `POST /api/cart/email-list/`, `/download-list/` | — | **dead endpoints: no matching Django route exists; these 404 in production** |

Three real forms. That is the whole conversion.

## What is missing entirely

`zod`, `react-hook-form` and `@freetheplatform/web-security` are all absent from
`frontend/package.json`. There are zero `*.schema.ts` files and zero `z.object(`
occurrences. There is no `FIELD_MAX` table on either side of the wire.

## FORMS-9/10/11 are n/a today, and saying so is the point

Those three rules govern Server Actions, the `lib/serverApi.ts` wrapper, and the
session cookies that wrapper forwards. splitcart has no Server Actions
(`'use server'` appears nowhere), no `serverApi.ts`, and no session cookies — it
authenticates with a bearer token in `localStorage` plus a plain JS-readable
`anonymousId` cookie.

So these are not unimplemented rules, they are rules whose preconditions do not
exist. They become applicable only when [`auth-migration.md`](auth-migration.md)
lands and the app has `splitcart_access` / `splitcart_refresh` cookies to
forward. The conformance ledger records them as `n/a` with that reason, not as
`fail`, and not as `pass`.

## Work

| #    | Work                                                                                                                                                                                       | Acceptance                                                                    |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| FM-1 | Fix the unvalidated cart-rename endpoint. `users/views/cart_viewset.py` reads `request.data.get('new_name')` and writes it to the model with no serializer and no bound. This is a live defect and does not wait for the forms conversion — it is also [`security.md`](security.md) SC-8. | The action validates through a serializer; a regression test covers the over-long input. |
| FM-2 | Delete the two dead cart-export endpoints' call sites in `FinalCartPage.tsx`, or implement the routes. They POST to `/api/cart/email-list/` and `/api/cart/download-list/`, neither of which is routed anywhere in Django. Decide which, then make the code tell the truth. | No client code calls an unrouted endpoint.                                    |
| FM-3 | Add `zod` to the frontend.                                                                                                                                                                 | Declared and exact-pinned per BASE-5.                                         |
| FM-4 | Decide splitcart's relationship to `freetheplatform.security.bounds`. FORMS-8 requires `FIELD_MAX` and the Python `bounds` module to declare the same kinds at the same values — but splitcart does not depend on the `freetheplatform` package at all (`requirements.txt` has no entry). Either onboard the dependency, or declare a local `FIELD_MAX` that mirrors the shared kinds exactly and record in the ledger that FORMS-8's cross-repo test cannot run yet. Do not silently invent a third vocabulary. | The decision is written down and the values match the shared table.           |
| FM-5 | Add `FIELD_MAX` to the frontend and bound the server side to match. Server-side today: `full_name` 255, `email` ~254 default, `password` 128 — none expressed as a `FIELD_MAX`-style kind. Ceilings use the right kind, not a number that happens to fit (FORMS-6, FORMS-7). | Every string field carries a `.max()` sourced from `FIELD_MAX`.               |
| FM-6 | Wrap the cart-rename input in a real `<form>` so it is a form rather than a bare `<Input>` firing a handler.                                                                                | Submits through form semantics; keyboard Enter works.                         |
| FM-7 | Convert all three forms to Track B with a colocated `*.schema.ts` beside each (FORMS-5). `z.object(` appears nowhere else without an exception row.                                        | Three schema files; three converted forms.                                    |
| FM-8 | Ship `check-forms.mjs` plus `scripts/forms/{form-ledger,form-hygiene,walk}.mjs`, adapted from freethedesk, and write the initial ledger. Every file rendering a `<form>` gets a row, and every row points at a file that renders one (FORMS-1). Rows that are not A or B carry a written reason (FORMS-2). | `npm run check:forms` exits 0; appended to `npm run check`.                   |

## Ledger rows to seed

Three `B` rows for the converted forms. Exclusion rows, each with its real
reason, for `NavSearchBar.tsx` (client-side navigation, no network write) and
`settings-dialog.tsx` (renders controls, submits nothing). `ContactPage.tsx` gets
no row at all — it is not a form and never was.
