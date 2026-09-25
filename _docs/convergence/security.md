# Convergence plan — security

**Type:** status and work plan. Non-normative. The binding rules are
[`../../../freetheplatform/_docs/security-standard.md`](../../../freetheplatform/_docs/security-standard.md).
Delete a row when it lands; delete this file when every row is gone.

Evidence for every claim below:
`scratchpad/gap-security.md` (survey of 2026-09-25).

## Scope split

This plan has two halves and they are not the same kind of work.

**Half A — configuration and boundary defects.** Mechanical, local, no
architectural decision. Land these now.

**Half B — the session model.** splitcart authenticates with a
non-expiring DRF `authtoken` held in `localStorage`. The standard (§3) requires
cookie-JWT sessions from `freetheplatform.auth`, a package splitcart does not
currently depend on. This is a real migration with a real blast radius and it is
planned separately in [`auth-migration.md`](auth-migration.md). Nothing in Half A
depends on it.

## Half A — land now

| #    | Work                                                                                                                                                                                             | Acceptance                                                                                                            |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| SC-1 | Gate `admin/` on `DEBUG` in `config/urls.py`, or move it behind an unguessable prefix read from the environment. Today it is routed unconditionally (§17).                                        | Production config does not expose `/admin/` at the default path.                                                      |
| SC-2 | Gate `debug_toolbar` and `django_extensions` on `DEBUG` — `INSTALLED_APPS`, `MIDDLEWARE`, and the `__debug__/` route. Both are commented out of `requirements.txt`, so prod either crashes on boot or runs a stale venv that exposes them. Resolve which, and record it. | `DEBUG=False` boots with neither installed, and neither appears in a production dependency set.                       |
| SC-3 | Add the missing transport and cookie settings under a `DEBUG`-aware block: `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS` (+ `INCLUDE_SUBDOMAINS`, `PRELOAD`), `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE`, `CSRF_COOKIE_SECURE`, `SECURE_PROXY_SSL_HEADER`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY`. Match freethedesk's block. | `manage.py check --deploy` is clean with `DEBUG=False`.                                                               |
| SC-4 | Set `X_FRAME_OPTIONS = "DENY"` (Django defaults to `SAMEORIGIN`).                                                                                                                                | Response carries `X-Frame-Options: DENY`.                                                                             |
| SC-5 | State `DATA_UPLOAD_MAX_MEMORY_SIZE` and `DATA_UPLOAD_MAX_NUMBER_FIELDS` explicitly rather than riding Django's defaults (§9).                                                                     | Both named in `config/settings.py` with a comment giving the reason for the value.                                    |
| SC-6 | Replace the catch-all throttle rates with named scopes. `anon: 5000/day` and `user: 20000/day` are not rate limiting; §5 forbids a catch-all. Add `login`, `register`, and `password_reset` scopes and apply them to those views. | Unauthenticated auth endpoints carry a scope measured in attempts per minute, not thousands per day.                 |
| SC-7 | Bound the registration password field. `dj_rest_auth`'s `RegisterSerializer` leaves it unbounded on an unauthenticated endpoint — an expensive-hash DoS vector.                                   | A `max_length` is enforced at the serializer boundary, with a regression test posting an over-long password.         |
| SC-8 | Fix `users/views/cart_viewset.py`. `rename`, `switch_active`, `sync` and `optimize` read `request.data.get(...)` straight into the model with no serializer and no bound — `rename` sets `cart.name` with no validation at all. Give each action a serializer. | Every action validates through a serializer; regression tests cover the over-long, wrong-type and missing-field paths. |
| SC-9 | Repair the dependency files: `requirements_dev.txt` is UTF-16LE and unreadable as UTF-8, and `drf-nested-routers` is unpinned in `requirements.txt`. Adopt the family's `.in` + `pip-compile` convention (`requirements.in`, `requirements-dev.in`). | Both files are UTF-8, fully pinned, and regenerable from a `.in` source.                                             |
| SC-10 | Add `.env*.local` to `frontend/.gitignore`. `frontend/.env.local` is untracked today only because an unrelated root rule happens to hide it — accidental safety, not a rule.                     | The pattern is explicit in the frontend ignore file.                                                                  |
| SC-11 | Emit security headers and a CSP from `frontend/next.config.ts` `headers()`. splitcart sends none today. Add `Cache-Control: no-store` on `/api/*`.                                               | Every response carries the standard header set; the CSP is built, not hand-written as a string, where a builder exists. |

`SC-11` is where `@freetheplatform/web-security`'s CSP builder would normally be
used. splitcart does not depend on the package yet. Land a local `headers()`
block now rather than blocking the whole row on the dependency decision, and
note the swap in [`auth-migration.md`](auth-migration.md).

## Half B — planned separately

| Item                                                          | Where                                          |
| ------------------------------------------------------------- | ---------------------------------------------- |
| Cookie-JWT sessions, account lockout, password reset, roles   | [`auth-migration.md`](auth-migration.md)       |
| Retiring CORS in favour of same-origin proxying               | [`auth-migration.md`](auth-migration.md)       |
| Edge route protection (`proxy.ts`)                            | [`auth-migration.md`](auth-migration.md)       |
| `FIELD_MAX` / shared bounds table                             | [`forms.md`](forms.md)                         |
| The §19 check suite                                           | [`auth-migration.md`](auth-migration.md)       |

## Why these are separated

§3 is the rule with the largest gap and the largest cost, and it is tempting to
treat everything else as blocked behind it. It is not. Every row in Half A is
independently correct, independently testable, and independently valuable — and
an unguarded `/admin/` in production does not become less urgent because the
session model is also wrong.
