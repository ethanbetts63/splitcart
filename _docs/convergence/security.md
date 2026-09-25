# Convergence plan — security

**Type:** status and work plan. Non-normative. The binding rules are
[`../../../freetheplatform/_docs/security-standard.md`](../../../freetheplatform/_docs/security-standard.md).
Delete a row when it lands; delete this file when every row is gone.

Evidence for every claim below:
`scratchpad/gap-security.md` (survey of 2026-09-25).

## Scope split

This plan has two halves and they are not the same kind of work.

**Half A — configuration and boundary defects.** Landed, except for the one row
below, which is the frontend's.

**Half B — the session model.** splitcart authenticates with a
non-expiring DRF `authtoken` held in `localStorage`. The standard (§3) requires
cookie-JWT sessions from `freetheplatform.auth`, a package splitcart does not
currently depend on. This is a real migration with a real blast radius and it is
planned separately in [`auth-migration.md`](auth-migration.md). Nothing in Half A
depends on it.

## Half A — land now

| #     | Work                                                                                                                                                                             | Acceptance                                                                                                              |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| SC-11 | Emit security headers and a CSP from `frontend/next.config.ts` `headers()`. splitcart sends none today. Add `Cache-Control: no-store` on `/api/*`.                                | Every response carries the standard header set; the CSP is built, not hand-written as a string, where a builder exists. |

`SC-11` is where `@freetheplatform/web-security`'s CSP builder would normally be
used. splitcart does not depend on the package yet. Land a local `headers()`
block now rather than blocking the whole row on the dependency decision, and
note the swap in [`auth-migration.md`](auth-migration.md).

Django's half of the header set is already in place: `SECURE_HSTS_SECONDS` is
`63072000` with `INCLUDE_SUBDOMAINS`, and `X_FRAME_OPTIONS` is `DENY`. The two
HSTS values must agree, so match that number rather than choosing one.

## Carried out of Half A

Two things the Half A work turned up that no row anticipated, and that belong to
plans other than this one.

- **`api/export/companies/` has no throttle scope.** It is the one remaining DRF
  route without one. `IsInternalAPIRequest` gates it, so it is not a public
  surface, but the §19 route-coverage check will flag it when that arrives.
- **`SECURE_SSL_REDIRECT` is `True` rather than silenced.** freethedesk silences
  `security.W008` because its host redirects at the edge; whether PythonAnywhere's
  "Force HTTPS" is on is not visible from this repository, so Django does the
  redirect here. If the host turns out to do it too, the duplicate is harmless —
  but the test suite will 301 every request on any checkout whose `.env` sets
  `DEBUG=False`.

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
treat everything else as blocked behind it. It is not. Every row in Half A was
independently correct, independently testable, and independently valuable — and
an unguarded `/admin/` in production did not become less urgent because the
session model is also wrong.
