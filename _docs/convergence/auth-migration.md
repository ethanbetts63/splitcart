# Convergence plan — session model

**Type:** closed record. Non-normative. The binding rule is
[`security-standard.md`](../../../freetheplatform/_docs/security-standard.md)
§3, with the capability contract in
[`apps/auth.md`](../../../freetheplatform/_docs/apps/auth.md) and
[`apps/web-security.md`](../../../freetheplatform/_docs/apps/web-security.md).

Every row landed on 2026-10-13. What follows is what was decided along the way,
for whoever next touches auth; the code and `users/README.md` say what it is.

## What it replaced

A DRF `authtoken` that never expired and was never rotated, returned in the
login body and kept in `localStorage`, where any script could read it. The
backend's logout did revoke, but the frontend never called it, so no token the
site issued was ever revoked. The browser called Django cross-origin, which is
the only reason CORS existed.

## What landed

| #    | Work                                                                                                      | Commit     |
| ---- | --------------------------------------------------------------------------------------------------------- | ---------- |
| AU-3 | Backend on `freetheplatform.auth` at `v0.35.0` (Django 6.0); dj-rest-auth, allauth and the authtoken gone | `20b9102f` |
| AU-4 | Frontend on `createAuthedFetch` and a same-origin `/api/*`; login and signup are Server Actions           | `7518a849` |
| AU-5 | `n/a`: no route needs a session, so `createProxy` would have no prefix to guard                           | —          |
| AU-6 | CORS removed, settings and middleware both                                                                | `20b9102f` |
| AU-7 | `lib/serverApi.ts` owns `DJANGO_API_URL` and forwards only `splitcart_access` / `splitcart_refresh`       | `7518a849` |
| AU-8 | `scripts/check-security.sh` runs the deploy checks as production sees them; the commit hook runs it       | `20b9102f` |

AU-0's four defects all closed by arriving rather than by separate fixes: the
two doors now pass the merger the same validated UUID, the merge is one
transaction, and the package's password change requires the current password
and ends every other session. Password reset, which had answered 500, works and
lands on `/reset-password/<uid>/<token>/`.

## Decisions worth keeping

- **The cart merge is splitcart's, in front of the package's login.**
  `users/views/auth_views.LoginView` subclasses the shared view, bounds the body
  before anything is hashed, and merges only after a 200. A failed merge rolls
  back and is logged; it never refuses the sign-in. An empty signed-out cart is
  not merged at all — every signed-out visit gets one, so signing out and back
  in used to stand the account's own list down for nothing.
- **`USERNAME_FIELD` is `email`,** so simplejwt reads an `email` key while the
  package's lockout looks the account up by `username`.
  `users/credentials.email_credentials` returns both.
- **The `/api/*` rewrite is in `proxy.ts`, not `next.config.ts`.** The standard
  accepts Vercel's address as a residual on the browser path. Here it would have
  made the per-IP cart and optimiser rates one bucket for every signed-out
  shopper, so the proxy forwards the visitor's address beside
  `FTP_PROXY_SECRET`, the same pair `serverApiFetch` sends.
- **`api/export/companies/` had no throttle scope.** `ftp_security.E006`
  refused to start until it took the pipeline's `internal` scope.

## Owed outside this repository

Deploying it is the owner's: see [`../to_do.md`](../to_do.md).
