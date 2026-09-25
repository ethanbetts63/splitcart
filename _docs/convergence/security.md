# Convergence plan — security

**Type:** status and work plan. Non-normative. The binding rules are
[`../../../freetheplatform/_docs/security-standard.md`](../../../freetheplatform/_docs/security-standard.md).
Delete a row when it lands; delete this file when every row is gone.

Evidence for every claim below:
`scratchpad/gap-security.md` (survey of 2026-09-25).

## Scope split

This plan has two halves and they are not the same kind of work.

**Half A — configuration and boundary defects.** Landed, except for the one row
below, which is Django's.

**Half B — the session model.** splitcart authenticates with a
non-expiring DRF `authtoken` held in `localStorage`. The standard (§3) requires
cookie-JWT sessions from `freetheplatform.auth`, the Python distribution, which
splitcart does not depend on — the npm package the header work brought in is the
other artifact built from that repository, not this one. This is a real migration with a real blast radius and it is
planned separately in [`auth-migration.md`](auth-migration.md). Nothing in Half A
depends on it.

## Half A — land now

| #      | Work                                                                                                                                                          | Acceptance                                                                                                         |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| SC-11b | Decide where `Cache-Control: no-store` for API responses belongs here, and put it there. The frontend cannot carry it, and a blanket rule is the wrong shape. | Every response holding one caller's data says `no-store`; no public catalogue response loses its deliberate cache. |

The header set and the CSP landed on 2026-09-25. `frontend/next.config.ts`
builds them with `securityHeaders()` from `@freetheplatform/web-security`,
which splitcart now depends on — pinned to `v0.19.0`, the tag the other three
repos are on. That closed `auth-migration.md`'s AU-1 and AU-2 ahead of the rest
of that plan, so a local `headers()` block never had to exist.

Django's half of the header set was already in place: `SECURE_HSTS_SECONDS` is
`63072000` with `INCLUDE_SUBDOMAINS` and matches the frontend's `max-age`, and
`X_FRAME_OPTIONS` is `DENY`.

### Why SC-11b is still open

The original row said "add `Cache-Control: no-store` on `/api/*`" alongside the
header set, on the assumption that the frontend could emit it. It cannot, and
a blanket rule would be wrong here even if it could. Two findings, both checked
rather than reasoned about:

- **Next cannot put a header on an externally-rewritten response.** Every
  `/api/*` path is rewritten to another origin, and Next 16 returns the
  upstream response byte for byte. Neither a `headers()` rule nor a `proxy.ts`
  `NextResponse.next()` header survives it — `curl -D -` against
  `next start` shows only Django's own headers. Both were tried. A rule in
  `next.config.ts` would look like the control and do nothing, so there is not
  one; the reason is written where somebody would go to add it.

  This is moot in production anyway. `lib/apiUrl.ts` builds an absolute URL to
  `api.splitcart.com.au`, so the browser never uses the rewrite and Next never
  sees an API response to put a header on.

- **A blanket `no-store` would delete a deliberate cache.** SEC §7 assumes every
  `/api/` response is one caller's data. splitcart's API is mostly a public
  price catalogue: six views carry `@cache_page` for two to twenty-four hours
  precisely because their answer does not depend on who is asking, and
  `config/tests/test_caching.py` records why that is the right shape. The
  per-caller views — auth, the cart viewset, the internal file exports —
  already carry `never_cache`, which emits `no-store` among the rest.

So the substance of §7 is met today, by the endpoints it exists to protect. What
is missing is §7's actual argument for a middleware over per-view decoration:
_"Per-view would mean the one view somebody forgot is the one that leaks."_
Nothing here enumerates per-caller views, so a new one that forgets `never_cache`
is cached by whatever sits in front of it and nobody is told.

The shape that fits both: a Django middleware that sets `no-store` only on a
response that has no explicit `Cache-Control` of its own. `@cache_page` and
`never_cache` both set one, so it changes nothing that already decided, and
makes forgetting safe by default instead of silent. It needs a test, and it is
Django's to carry rather than the frontend's — which is why it is a row here
rather than something the SC-11 work quietly did on its way past.

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

| Item                                                        | Where                                    |
| ----------------------------------------------------------- | ---------------------------------------- |
| Cookie-JWT sessions, account lockout, password reset, roles | [`auth-migration.md`](auth-migration.md) |
| Retiring CORS in favour of same-origin proxying             | [`auth-migration.md`](auth-migration.md) |
| Edge route protection (`proxy.ts`)                          | [`auth-migration.md`](auth-migration.md) |
| `FIELD_MAX` / shared bounds table                           | [`forms.md`](forms.md)                   |
| The §19 check suite                                         | [`auth-migration.md`](auth-migration.md) |

## Why these are separated

§3 is the rule with the largest gap and the largest cost, and it is tempting to
treat everything else as blocked behind it. It is not. Every row in Half A was
independently correct, independently testable, and independently valuable — and
an unguarded `/admin/` in production did not become less urgent because the
session model is also wrong.
