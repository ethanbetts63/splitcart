#!/usr/bin/env bash
#
# Vercel's install step. Shared engine -- edit it in freetheplatform/frontend/registry/tooling/ and re-sync.
#
# @freetheplatform/web-security is a private repo pinned in package-lock.json to git+ssh://, and Vercel's build
# container has no SSH key, so a plain `npm install` dies with "Permission denied (publickey)". The rewrite below
# points git at authenticated HTTPS; the lockfile is untouched and local development keeps resolving over SSH.
#
# A file, not an inline vercel.json installCommand: that field is capped at 256 characters and would put the
# expanded token in the build log.
set -euo pipefail

if [ -z "${GH_TOKEN:-}" ]; then
  echo "GH_TOKEN is not set on this Vercel project." >&2
  echo "It wants a fine-grained GitHub token with Contents:read on" >&2
  echo "ethanbetts63/freetheplatform. See freetheplatform/_docs/deployment-standard.md." >&2
  exit 1
fi

git config --global --add \
  "url.https://x-access-token:${GH_TOKEN}@github.com/.insteadOf" \
  "ssh://git@github.com/"

npm install
