# To do

Open tasks for this repository. Append any you find; delete one once you know it's done.

## Deploying the session migration (2026-10-13)

`main` was pushed on 2026-10-13, so Vercel may already be building the new
frontend while PythonAnywhere still runs the July backend. Until step 3 is done,
signing in and signing up fail in production: the old API has no `/api/token/`.
In this order, because the frontend speaks only the new protocol:

1. **Python package access on PythonAnywhere.** `requirements.txt` now installs
   `freetheplatform` from its private GitHub repository at `v0.35.0`. The
   console needs the `GH_TOKEN` `insteadOf` entry in `~/.gitconfig` that
   `../freetheplatform/_docs/deployment-standard.md` describes — exactly one —
   unless this account already has it for another site.
2. **`FTP_PROXY_SECRET`.** It exists nowhere yet: generate one value with
   `python -c "import secrets; print(secrets.token_urlsafe(48))"` and put the
   same string in two places — the server's `.env` at the repository root
   (beside `SECRET_KEY`; `settings.py` reads it through `load_dotenv`), and
   Vercel → splitcart project → Settings → Environment Variables, Production,
   as a plain (not `NEXT_PUBLIC_`) variable.
   Without it every request is attributed to Vercel and the cart rates become
   one bucket for everyone.
3. **Backend.** On the server: `git pull`, install `requirements.txt`, run
   `manage.py migrate` (adds the token blacklist and `ftp_auth` tables) and
   `scripts/check-security.sh`, and reload the web app.
4. **Vercel.** Delete `NEXT_PUBLIC_DJANGO_API_URL`; keep `DJANGO_API_URL`
   pointing at `https://api.splitcart.com.au`. Then redeploy the frontend so it
   picks up both variables.
5. **Everyone is signed out once.** The old DRF tokens stop working; signing in
   again is the whole recovery. Carts are untouched.
6. **Optional cleanup.** The `authtoken_token`, `account_*`, `socialaccount_*`
   and `django_site` tables are orphaned and can be dropped once the deploy has
   settled.
