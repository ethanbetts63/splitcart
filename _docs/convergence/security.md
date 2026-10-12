# Convergence plan — security

**Type:** closed record. Non-normative. The binding rules are
[`../../../freetheplatform/_docs/security-standard.md`](../../../freetheplatform/_docs/security-standard.md).
Delete a row when it lands; delete this file when every row is gone.

Evidence for every claim below:
`scratchpad/gap-security.md` (survey of 2026-09-25).

## Scope split

This plan has two halves and they are not the same kind of work.

**Half A — configuration and boundary defects.** Landed.

**Half B — the session model.** Landed 2026-10-13: cookie-JWT sessions from
`freetheplatform.auth`, recorded in [`auth-migration.md`](auth-migration.md).
Nothing in Half A depended on it.

## Half A — landed

The header set and the CSP landed on 2026-09-25. `frontend/next.config.ts`
builds them with `securityHeaders()` from `@freetheplatform/web-security`,
which splitcart now depends on, at the tag the other three repos are on. That closed `auth-migration.md`'s AU-1 and AU-2 ahead of the rest
of that plan, so a local `headers()` block never had to exist.

Django's half of the header set was already in place: `SECURE_HSTS_SECONDS` is
`63072000` with `INCLUDE_SUBDOMAINS` and matches the frontend's `max-age`, and
`X_FRAME_OPTIONS` is `DENY`.

§7's `Cache-Control` clause landed on 2026-09-26 as
`config.middleware.NoCacheApiMiddleware`, which gives an `/api/` response
`no-store, private` only when it carries no `Cache-Control` of its own. It could
not be the frontend's: Next 16 returns an externally-rewritten response byte for
byte, so no `headers()` rule survives `proxy.ts`'s rewrite of `/api/*`. The
reason is recorded in `next.config.ts`, where somebody would go to add the rule
that does nothing.

It could not be a blanket rule either. splitcart's API is mostly a public price
catalogue and six views carry `@cache_page` for two to twenty-four hours, which
an unconditional overwrite — the shape allbikes and bloomprint use — would
delete. Deferring to a response that already decided keeps those, leaves the
`never_cache` views exactly as they are, and still answers §7's actual argument
for a middleware: the view somebody forgets now says `no-store` instead of being
cached by whatever sits in front of it while nobody is told. Both directions are
tested in `config/tests/test_caching.py`.

## Carried out of Half A

- **`api/export/companies/` had no throttle scope.** `ftp_security.E006` found
  it when the §19 checks arrived, and it took the pipeline's `internal` scope.
- **`SECURE_SSL_REDIRECT` is `True` rather than silenced.** freethedesk silences
  `security.W008` because its host redirects at the edge; whether PythonAnywhere's
  "Force HTTPS" is on is not visible from this repository, so Django does the
  redirect here. If the host turns out to do it too, the duplicate is harmless —
  but the test suite will 301 every request on any checkout whose `.env` sets
  `DEBUG=False`.

## Why these are separated

§3 is the rule with the largest gap and the largest cost, and it is tempting to
treat everything else as blocked behind it. It is not. Every row in Half A was
independently correct, independently testable, and independently valuable — and
an unguarded `/admin/` in production did not become less urgent because the
session model is also wrong.
