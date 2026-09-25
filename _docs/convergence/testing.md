# Convergence plan — testing

**Type:** status and work plan. Non-normative. The binding rules are
[`testing-standard-backend.md`](../../../freetheplatform/_docs/testing-standard-backend.md)
(TESTB-1..9) and
[`testing-standard-frontend.md`](../../../freetheplatform/_docs/testing-standard-frontend.md)
(TESTF-1..5).

TS-1 through TS-8 have landed. The backend suite runs from a clean clone, the
`users/` hole is closed, and `npm run check` is green. What is left is one half
of one frontend row, and a manual step nobody with a keyboard can do.

## Work

| #    | Work                                                                                                                                                                                                                                                                                                                           | Acceptance                                                        |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------- |
| TS-9 | The `check:sitemap` half landed with [`seo.md`](seo.md) — 15 routes, all resolving. The login/signup form-versus-serializer contract check did not. It is the same script [`forms.md`](forms.md) FM-8 owns, so it lands there rather than being written twice; this row is the note that the testing side of it is still owed. | `npm run check:forms` exists, exits 0, and is in `npm run check`. |

## Outstanding, and not an agent's to do

**No developer machine can run this suite against MySQL.** The MySQL user is
granted `allbikes`, `bloomprint`, `freethedesk` and their `test_` counterparts,
and nothing for splitcart, so `CREATE DATABASE test_splitcart` is refused.
`mysqlclient` is the second half of the same wall: a C extension with no wheel
for the Python installed here.

The suite therefore runs on in-memory SQLite, deliberately and in writing — see
[`../TESTING.md`](../TESTING.md#which-database-the-tests-run-against) for what
that costs and how to opt back out with `SPLITCART_TEST_DB=mysql`. Granting
`ALL PRIVILEGES ON test_splitcart.*` is a one-line administrative step, and
until someone takes it no run here has exercised the engine the site runs on.

## Defects the tests turned up

Recorded here because the plans that would own them —
[`security.md`](security.md) and [`dead-code.md`](dead-code.md) — have closed.
Each is described in full where it was found.

**Django's whole-site cache served one caller's data to another. Fixed.**
`UpdateCacheMiddleware` and `FetchFromCacheMiddleware` stored any 200 answering
a GET under a key built from the URL and the response's `Vary` headers. Token
authentication never touches the session, so no `Vary: Cookie` was ever added
and every caller computed the same key. Three live consequences were found: one
shopper's cart served to everyone (`/api/carts/active/`, `/api/carts/`), one
account's email address served to everyone (`/api/auth/user/`), and a
regenerated translation table withheld from the scraper for ten minutes
(`/api/files/*`). Each was closed at the view with `never_cache`, and the
middleware itself has since been removed so the next per-caller GET is safe by
default. Nothing was lost: the public read-only endpoints already carry their
own `@cache_page`. `config/tests/test_caching.py` keeps it removed.

**`POST /api/auth/password/reset/` answers 500.** Live, unauthenticated, and
throttled, but the email builder reverses `password_reset_confirm` and nothing
routes that name. Behind it is a product gap: there is no frontend page for a
reset link to land on. `users/tests/view_tests/test_password_reset.py` holds
the detail and an `xfail(strict=True)` assertion of what is owed.

**Registering with an email that already has an account answered 500.** Fixed,
because the fix was unambiguous: dj-rest-auth's uniqueness check asks whether
the address is _verified_, and `ACCOUNT_EMAIL_VERIFICATION` is `'none'`, so it
never fired and the INSERT hit the unique constraint.
`CustomRegisterSerializer.validate_email` now checks the user table.

**Signing up loses the cart; logging in keeps it.** The anonymous-cart merge
hangs off `CustomLoginSerializer.validate()`, and the signup form posts to
`/api/auth/registration/`, which takes no `anonymous_id` and never calls login.
A shopper who fills a cart signed out and then creates an account loses it.
Product decision, not a defect in the merge — and directly relevant to
[`auth-migration.md`](auth-migration.md), which deletes the class the merge
lives on. The behaviour itself is pinned independently in
`users/tests/util_tests/test_session_merger.py`.

**`/api/carts/` paginated an unordered queryset. Fixed.** `Cart` declared no
`Meta.ordering`, so DRF warned on every list request and a second page could
repeat or drop rows. It now orders by `['-updated_at', 'id']` — most recently
touched first, which is the order a cart list is read in, with `id` as the
tiebreaker because `updated_at` alone is not unique.
