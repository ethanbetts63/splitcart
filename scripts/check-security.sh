#!/bin/sh
#
# Run the deployment and security checks the way production would see them.
#
# Every check worth having here is a no-op under DEBUG -- local work runs on
# plain HTTP -- and `.env` sets DEBUG=True, so a plain `manage.py check --deploy`
# reports nothing while looking exactly like a pass.
#
# This covers Django's own deployment checks and freetheplatform's: cookies and
# TLS, the unrouted admin, the authentication classes, the throttle cache, the
# proxy secret, and ftp_security.E006, which refuses a route with no throttle
# scope. It reads settings and the URLconf and opens no database connection, so
# it takes seconds.
#
# `settings_test` rather than `config.settings` only because the latter imports
# the MySQL driver, which has no wheel for this machine's Python; it is
# `config.settings` with a different DATABASES and nothing else.
#
# There is no CI here; see ../freetheplatform/_docs/security-standard.md,
# section 19. The pre-commit hook runs this when Python is staged.

set -e
cd "$(git rev-parse --show-toplevel)"

random() { ./venv/Scripts/python -c "import secrets; print(secrets.token_urlsafe($1))"; }

# python-dotenv does not overwrite a variable already in the environment, so
# these win over .env. A long random SECRET_KEY because security.W009 fires on a
# short one, and the key in .env is a local one -- production's lives in the
# PythonAnywhere environment. FTP_PROXY_SECRET for the same reason:
# ftp_security.W008 fires while it is unset.
DEBUG=False \
SECRET_KEY="$(random 64)" \
FTP_PROXY_SECRET="$(random 48)" \
    ./venv/Scripts/python manage.py check --deploy --fail-level WARNING --settings=settings_test
