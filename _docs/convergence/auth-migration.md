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
- **It never expires.** There is no rotation, no TTL, no refresh.
- **Logout does not log out.** The client clears its copy; the server-side token
  row is never revoked. A token captured at any point stays valid indefinitely.

The third is the one that turns the first into a durable compromise rather than
a session-length one.

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
- and carries one piece of product behaviour (the cart merge) that no test
  currently covers — `users/` has no tests at all, per
  [`testing.md`](testing.md).

That last point is decisive. **[`testing.md`](testing.md) TS-3 is a hard
prerequisite.** Migrating untested auth and cart-merge logic means the migration
has no way to prove it preserved behaviour, and the first signal would be users
losing carts in production.

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
| AU-0 | Cover `users/` — auth, the nine `CartViewSet` actions, and the anonymous-cart-merge behaviour — with the tests that will prove the migration preserved behaviour. | —                            |
| AU-3 | Migrate the backend session model; re-home the cart-merge hook explicitly, with its own test.                                                                     | AU-0                         |
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
