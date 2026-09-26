#!/usr/bin/env bash
#
# Vercel's install step.
#
# Shared engine -- edit it in freetheplatform/frontend/registry/tooling/ and
# re-sync, never in a product. Every repo in the family installs the same
# private dependency the same way.
#
# @freetheplatform/web-security lives in a private repository, and
# package-lock.json pins it to git+ssh://git@github.com/... -- the protocol npm
# recorded when the lockfile was written on a machine that had an SSH key.
# Vercel's build container has no SSH key, and carries a credential only for the
# repository being deployed, so a plain `npm install` dies with
# "Permission denied (publickey)".
#
# The rewrite below points git at authenticated HTTPS instead. npm still asks
# for the SSH URL and still verifies the same commit, so package.json and the
# lockfile are untouched and local development keeps resolving over SSH.
#
# This is a file rather than an inline vercel.json installCommand because that
# field is capped at 256 characters, and because keeping it out of the command
# keeps the expanded token out of the build log.
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
