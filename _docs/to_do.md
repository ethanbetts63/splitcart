# To do

Open tasks for this repository. Append any you find; delete one once you know it's done.

## Deploying the session migration (2026-10-13)

`main` is ahead of `origin` and nothing is pushed; production still runs the
July build. In this order, because the frontend speaks only the new protocol:

1. **Python package access on PythonAnywhere.** `requirements.txt` now installs
   `freetheplatform` from its private GitHub repository at `v0.35.0`. The
   console needs the `GH_TOKEN` `insteadOf` entry in `~/.gitconfig` that
   `../freetheplatform/_docs/deployment-standard.md` describes — exactly one —
   unless this account already has it for another site.
2. **`FTP_PROXY_SECRET`.** Generate one value (32+ random characters) and set it
   in the PythonAnywhere web app's environment and in Vercel's (server-only).
   Without it every request is attributed to Vercel and the cart rates become
   one bucket for everyone.
3. **Backend.** Push, then on the server: install `requirements.txt`, run
   `manage.py migrate` (adds the token blacklist and `ftp_auth` tables) and
   `scripts/check-security.sh`, and reload the web app.
4. **Vercel.** Delete `NEXT_PUBLIC_DJANGO_API_URL`; keep `DJANGO_API_URL`
   pointing at `https://api.splitcart.com.au`. Then deploy the frontend.
5. **Everyone is signed out once.** The old DRF tokens stop working; signing in
   again is the whole recovery. Carts are untouched.
6. **Optional cleanup.** The `authtoken_token`, `account_*`, `socialaccount_*`
   and `django_site` tables are orphaned and can be dropped once the deploy has
   settled.
