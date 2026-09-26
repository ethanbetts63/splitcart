# Convergence plan — session model

**Type:** status and work plan. Non-normative. The binding rule is
[`security-standard.md`](../../../freetheplatform/_docs/security-standard.md) §3,
with the capability contract in
[`apps/auth.md`](../../../freetheplatform/_docs/apps/auth.md) and
[`apps/web-security.md`](../../../freetheplatform/_docs/apps/web-security.md).

Evidence: `scratchpad/gap-security.md`, `gap-forms.md` (surveys of 2026-09-25).

This is the largest single item in the convergence and the only one held back
from the unattended sweep. It is specified here in full so the decision is
costed, not so it is deferred indefinitely.

## What splitcart does today

`rest_framework.authtoken` issues a token that never expires and is never
rotated. It is returned in the login response body, written to `localStorage`
by `AuthContext.tsx`, and sent as `Authorization: Token <token>` by
`apiClient.ts`.

Three consequences follow, and they compound:

- **Any XSS reads it.** `localStorage` is script-readable by construction. An
  httpOnly cookie is not.
- **It never expires.** There is no rotation, no TTL, no refresh. Logging in
  again returns the same key rather than a new one.
- **Nothing ever calls logout.** `POST /api/auth/logout/` does revoke — it
  deletes the `Token` row, and the credential is refused on the next request,
  which `users/tests/view_tests/test_auth_session.py` asserts. But
  `AuthContext.tsx` clears `localStorage` and posts nothing at all, so no token
  this site has ever issued has been revoked. A token captured at any point
  stays valid indefinitely.

The third is the one that turns the first into a durable compromise rather than
a session-length one — and note where it has to be fixed. The backend half
already works; AU-4 is what makes the browser use it.

Alongside it: an `anonymousId` in a plain JS-readable cookie, and direct
browser-to-Django calls over `NEXT_PUBLIC_DJANGO_API_URL` that bypass the
same-origin `/api/*` rewrite already sitting unused in `next.config.ts`.

## What the standard requires

Cookie-JWT sessions from `freetheplatform.auth`: short-lived access token and
rotating refresh token, both httpOnly, both same-origin, with server-side
revocation. Plus account lockout, a password reset flow, and a role-bearing
principal — all of which ship in the same package.

## Blast radius

Backend:

- Remove `allauth`, `dj_rest_auth` and `rest_framework.authtoken` from
  `INSTALLED_APPS`; add `freetheplatform` to `requirements.txt`.
- Rewrite `users/urls.py`.
- Delete `users/adapter.py`, `custom_login_serializer.py`,
  `custom_register_serializer.py`.
- **Re-home the anonymous-cart-merge hook.** It currently piggybacks on
  `CustomLoginSerializer.validate()`. This is the subtle one: it is real product
  behaviour hiding inside a class the migration deletes, and losing it silently
  drops a signed-in user's pre-login cart.

Frontend:

- Rewrite `AuthContext.tsx` and both auth forms onto `createAuthedFetch`.
- Route browser traffic through the existing same-origin `/api/*` rewrite.
- Add `frontend/src/proxy.ts` using `createProxy` from
  `@freetheplatform/web-security/proxy` for edge route protection — splitcart
  has no `middleware.ts`/`proxy.ts` at all, so protected routes are gated
  client-side after hydration, which is not gating.

Then CORS disappears. `CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_HEADERS` and the
`corsheaders` middleware exist only because the browser calls Django
cross-origin. Same-origin proxying removes the reason for them, and the
standard's position is that a correctly-shaped frontend needs no CORS at all.

## Why it is sequenced last

Every other plan in this directory is independently landable, independently
testable, and independently valuable. This one:

- migrates the backend onto the `freetheplatform` Python distribution, a
  dependency splitcart has never had and a strategy-level decision rather than
  a code change — the npm half is already in, which settles the pinning
  convention but none of this;
- rewrites the login path of a live site, where a mistake logs out every user
  or, worse, fails open;
- has no staging environment in evidence to rehearse against;
- and carries one piece of product behaviour (the cart merge) whose whole
  failure mode is being lost quietly.

That last point was decisive, and it is the point AU-0 answered. `users/` now
carries 238 tests, and the cart merge is pinned at three layers: as a function
(`util_tests/test_session_merger.py`), at each serializer that currently calls
it, and — the layer that survives this migration —
`view_tests/test_anonymous_cart_at_both_doors.py`, which drives login and
registration through `reverse()` and names no serializer, method or module.
Whatever replaces those classes has to keep that file green.

## What AU-0 found

Four things, none of them fixed by AU-0, all of them AU-3's. Each is recorded
where it was found, as an `xfail(strict=True)` holding the assertion that is
owed, so that fixing one fails loudly rather than leaving the note behind.

- **The two doors disagree about the same identifier.**
  `CustomLoginSerializer.validate()` reads `anonymous_id` from
  `self.initial_data` — the raw string as posted — while
  `CustomRegisterSerializer.save()` reads `validated_data` and gets a canonical
  `uuid.UUID`. Both declare the field as a `UUIDField`, so both accept an
  upper-case spelling and neither reports a problem; only registration then
  finds the cart. The re-homing has to pick one behaviour knowing there were
  two. `view_tests/test_anonymous_cart_at_both_doors.py`.
- **The merge is not atomic.** `merge_anonymous_session` stands the user's own
  active cart down first, then creates, moves and deletes, with no
  `transaction.atomic()` and only `Cart.DoesNotExist` caught. A failure after
  the first write leaves the shopper with no active cart and the list they had
  switched off. `util_tests/test_session_merger.py`.
- **A password change does not require the current password.**
  `REST_AUTH['OLD_PASSWORD_FIELD_ENABLED']` is unset, so dj-rest-auth drops the
  field: a stolen token takes the account rather than merely reading it.
  [`security-standard.md`](../../../freetheplatform/_docs/security-standard.md)
  §3 requires it. `view_tests/test_password_change.py`.
- **A password change ends no other session.**
  `REST_AUTH['LOGOUT_ON_PASSWORD_CHANGE']` is likewise unset. Same file, same
  section of the standard. It cannot land on its own — the frontend holds its
  token in `localStorage` and would carry on presenting a revoked one — which
  is why it waits for AU-3 and AU-4 rather than being a settings edit.

`freetheplatform.auth` supplies all four by default, so AU-3 closes them by
arriving rather than by fixing anything.

One correction to the row this section replaces: it said "the nine
`CartViewSet` actions". There are eleven method/route pairs across the seven
URLs `SimpleRouter` generates — ten if `PUT` and `PATCH` are counted as one
operation. The nine appears to have been the five `@action`s plus the four
inherited operations the class writes code for (`get_queryset` serves list and
retrieve, `perform_create`, `perform_destroy`); `update` and `partial_update`
are the two with no override, and they were the two with no test.
`view_tests/test_cart_detail_writes.py` covers them.

## Sequence

AU-1 and AU-2 are gone: they landed on 2026-09-25, out of order, because
[`security.md`](security.md)'s header row needed the CSP builder and there was
no reason to hand-write a policy while waiting for the session work. The
dependency is `@freetheplatform/web-security` at `github:ethanbetts63/freetheplatform#v0.19.0`
— a pinned tag, the same one allbikes, bloomprint and freethedesk are on. That
answers "pinned tag, not branch" for everything below; what it does not answer
is whether the Python distribution should arrive, which is AU-3's question and
a much larger one.

| #    | Work                                                                                                                                                              | Blocked on                   |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| AU-3 | Migrate the backend session model; re-home the cart-merge hook explicitly, with its own test.                                                                     | —                            |
| AU-4 | Migrate the frontend onto `createAuthedFetch` and the same-origin rewrite.                                                                                        | AU-3                         |
| AU-5 | Add `proxy.ts` edge route protection.                                                                                                                             | AU-4                         |
| AU-6 | Remove CORS entirely.                                                                                                                                             | AU-4                         |
| AU-7 | FORMS-9/10/11 become applicable; implement `lib/serverApi.ts` forwarding `splitcart_access` and `splitcart_refresh` as a literal list, never the jar.             | AU-4, [`forms.md`](forms.md) |
| AU-8 | The §19 check suite (`ftp_security.*`, `ftp_auth.*`) arrives with the package; wire it into the verification table.                                               | AU-3                         |

## What lands without it

[`security.md`](security.md) Half A closes the unguarded admin route, the
unconditional debug toolbar, the absent transport settings, the catch-all
throttles, the unbounded registration password and the unserialized cart write —
none of which depend on the session model. splitcart is meaningfully safer
before AU-0 starts.
