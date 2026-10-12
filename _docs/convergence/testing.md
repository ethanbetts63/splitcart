# Convergence plan — testing

**Type:** status and work plan. Non-normative. The binding rules are
[`testing-standard-backend.md`](../../../freetheplatform/_docs/testing-standard-backend.md)
(TESTB-1..9) and
[`testing-standard-frontend.md`](../../../freetheplatform/_docs/testing-standard-frontend.md)
(TESTF-1..5).

Every row has landed. The backend suite runs from a clean clone, the `users/`
hole is closed, and `npm run check` is green with twelve checks in it. What is
left is a manual step nobody with a keyboard can do.

TS-9 closed last: the form-versus-serializer contract check
(`npm run check:form-contract`) now holds all three Track B forms against the
DRF serializers they post to. It is a separate command from `check:forms`
rather than part of it, because it runs `venv/Scripts/python` to import the
serializers — and `check:forms` is a name
[`forms-standard.md`](../../../freetheplatform/_docs/forms-standard.md) gives
the same four Node-only checks in every repository.

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
authentication never touched the session, so no `Vary: Cookie` was ever added
and every caller computed the same key. Three live consequences were found: one
shopper's cart served to everyone (`/api/carts/active/`, `/api/carts/`), one
account's email address served to everyone (`/api/auth/user/`), and a
regenerated translation table withheld from the scraper for ten minutes
(`/api/files/*`). Each was closed at the view with `never_cache`, and the
middleware itself has since been removed so the next per-caller GET is safe by
default. Nothing was lost: the public read-only endpoints already carry their
own `@cache_page`. `config/tests/test_caching.py` keeps it removed.

**Password reset answered 500.** The email builder reversed a URL name nothing
routed, and there was no page for a link to land on. Fixed by the session
migration: the package's reset sends `users/notifications.py`'s email, linking
to `/reset-password/<uid>/<token>/`.

**Registering with an email that already has an account answered 500.** Fixed,
because the fix was unambiguous: dj-rest-auth's uniqueness check asks whether
the address is _verified_, and `ACCOUNT_EMAIL_VERIFICATION` is `'none'`, so it
never fired and the INSERT hit the unique constraint.
Registration's serializer now checks the user table.

**Signing up lost the cart; logging in kept it.** The anonymous-cart merge hung
off login alone. Both doors now carry `anonymous_id` and call the same merger,
and `users/tests/view_tests/test_anonymous_cart_at_both_doors.py` holds them
together.

**`/api/carts/` paginated an unordered queryset. Fixed.** `Cart` declared no
`Meta.ordering`, so DRF warned on every list request and a second page could
repeat or drop rows. It now orders by `['-updated_at', 'id']` — most recently
touched first, which is the order a cart list is read in, with `id` as the
tiebreaker because `updated_at` alone is not unique.
