# Convergence plan — forms

**Type:** status and work plan. Non-normative. The binding rules are
[`forms-standard.md`](../../../freetheplatform/_docs/forms-standard.md)
(FORMS-1..11).

Evidence: `scratchpad/gap-forms.md` (survey of 2026-09-25).

The conversion landed on 2026-09-25. Three forms, three schemas, a `FIELD_MAX`
mirror on both sides of the wire, and `npm run check:forms` as the eleventh
check. Verdicts are in
[`../../../freetheplatform/_docs/conformance/splitcart.md`](../../../freetheplatform/_docs/conformance/splitcart.md).
One row is left, and two facts are worth keeping until the work that closes
them lands.

## Work

| #    | Work                                                                                                                                                                                                                                              | Acceptance                                 |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| FM-2 | Delete the two dead cart-export call sites. They POST to `/api/cart/email-list/` and `/api/cart/download-list/`, neither of which is routed anywhere in Django — verified again on 2026-09-25 against `config/urls.py` and every app's `urls.py`. | No client code calls an unrouted endpoint. |

**The decision is delete, not implement.** `email-list` would need a template
and a send; `download-list` would need a PDF library, and `requirements.txt`
has none — nothing in this repository renders a document. That is a feature to
build if the product wants it, not a route to restore, and it should not be
built by a plan whose subject is forms.

**What blocked it.** The deletion is not local to `FinalCartPage.tsx`. It runs
through `components/ResultsDisplay.tsx` (the `ExportButtons` component and
three required props), `context/CartContext.tsx`, `services/cart.api.ts`,
`ApiClient.postAndGetBlob`, and the `ExportData`/`ExportAction` types. The
component half sits in the file range a concurrent registry-adoption agent held
exclusively on 2026-09-25, so it was left rather than raced. It needs one pass
over all six files, which is also why it is listed as a single row in
[`dead-code.md`](dead-code.md) DC-7 rather than split.

## Two things that are true until the session model changes

**FORMS-8 is `n/a`, and the mirror is what stands in for it.** The rule is a
test in `freetheplatform`'s own suite comparing its `security.bounds` to
`@freetheplatform/web-security`. splitcart installs neither, and
[`../../AGENTS.md`](../../AGENTS.md) says adding one applies `strategy.md`'s
tests first — a larger question than bounding three forms. So the table is
mirrored kind for kind and value for value in `users/serializers/bounds.py` and
`frontend/src/lib/fieldMax.ts`, and `users/tests/serializer_tests/test_bounds.py`
pins both against one literal copy, the TypeScript one read off disk. What no
test here can see is the shared table moving. Both files name what to delete
when the dependency arrives.

**FORMS-10 and FORMS-11 are `n/a`; FORMS-9 is `fail`.** The first two have no
subject: no `serverApiFetch` to import, no session cookies to forward — auth is
a DRF token in `localStorage` that client JavaScript attaches. That is also why
the three converted forms run `useActionState` over a _client_ action rather
than a Server Action; every other part of Track B is the standard's shape
verbatim, and each form says so at the top.

FORMS-9 is different, and the original survey called it wrong. Four route files
(`app/page.tsx`, `app/bargains/page.tsx`, `app/categories/[slug]/page.tsx`,
`app/product/[slug]/page.tsx`) do read a server-side `DJANGO_API_URL` inline,
each with its own `localhost` fallback — which is exactly the split the rule
exists to prevent. There is no owning module: `lib/apiUrl.ts` owns
`NEXT_PUBLIC_DJANGO_API_URL`, a different variable for the browser.
`check-forms.mjs` carries the four as exception rows with that reason, so the
consolidation has a list to work from. The owner is the `lib/serverApi.ts` that
[`auth-migration.md`](auth-migration.md) creates.

## One engine is adapted, not copied

`scripts/forms/form-ledger.mjs` and `walk.mjs` are byte-identical to the shared
registry copies. `form-hygiene.mjs` is not: its fourth check reads
`src/lib/serverApi.ts` unconditionally, so the shared copy would crash on a
missing file rather than report FORMS-10/11 as `n/a`. splitcart's copy makes
`sessionCookies` optional and says so at the top; the registry's own sync
exclusions carry the same reason. When the wrapper exists, pass the cookies and
take the byte-identical copy.
