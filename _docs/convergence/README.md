# Convergence — splitcart

**Type:** migration tracking. Non-normative. The binding policies live in
[`../../../freetheplatform/_docs/`](../../../freetheplatform/_docs/README.md)
and are never restated here.

This directory is the single record of bringing splitcart onto the shared
engineering policies that already govern allbikes, bloomprint and freethedesk.
It is a to-do list with evidence attached. Delete a row when it lands; delete a
plan when its rows are gone; delete this directory when there is nothing left.

Surveyed 2026-09-25 against the standards as they stood that day.

**State as of 2026-09-26: eight of the ten plans are closed.** Eight rows
remain, in three plans — `auth-migration.md` (six), `registry.md` (one, waiting
on a `font-weight-*` ramp) and `dead-code.md` (one, waiting on a Search Console
traffic check, not on code). The closed plans are kept rather than deleted where
their emptied tables were replaced by a record of what landed and why; the
deletion this file asks for is owed once that record has somewhere better to
live.

## The one-paragraph summary

splitcart was never on these policies — it was not drifting from them. It sat
outside the shared-package graph entirely until 2026-09-25, when the header work
brought in `@freetheplatform/web-security`; the Python side is still untouched,
so that remains one npm package rather than a shared session model. Its frontend
had completed a Vite-to-Next migration that never reached its documentation, its
configuration, or its dead routes. Its design tokens were unmodified
`shadcn init` output. It had no formatter, no CSS lint, no structural checks, no
`AGENTS.md`, and no tests for the app that owns authentication and carts.

None of that was unusual for a repo brought in late, and most of it was cheap.

All of the above has since landed. `npm run check` runs twelve checks; the token
vocabulary is semantic, holds the family's one type ladder under a check that
fails in all four repos when it diverges, and carries a role-named width scale
so the space ramp cannot shadow a container width; `users/` has 238 tests. What
is left is the one item that was always going to be last — the session model —
plus two rows that are waiting on something other than effort.

## The plans

| Plan                                     | Owns                                                                                                   | State  |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------ | ------ |
| [`dead-code.md`](dead-code.md)           | Vite-era residue, including a catch-all route that turns 404s into 500s                                | 1 row  |
| [`security.md`](security.md)             | Configuration and boundary defects — admin exposure, transport settings, throttles, unvalidated writes | closed |
| [`tooling.md`](tooling.md)               | Prettier, stylelint, eslint, tsconfig, the dependency baseline, `npm run check`                        | closed |
| [`docs-hygiene.md`](docs-hygiene.md)     | `AGENTS.md`, the factually wrong README, broken links, the conformance ledger                          | closed |
| [`seo.md`](seo.md)                       | The page registry, sitemap, robots, and four uncoordinated JSON-LD emitters                            | closed |
| [`tokens.md`](tokens.md)                 | The semantic token vocabulary, the nine text rungs, and the sweep onto them                            | closed |
| [`testing.md`](testing.md)               | The missing `users/` test suite and the frontend check pipeline                                        | closed |
| [`forms.md`](forms.md)                   | Three forms, their schemas, and the field bounds table                                                 | closed |
| [`registry.md`](registry.md)             | Becoming a registry consumer, gated on tokens                                                          | 1 row  |
| [`auth-migration.md`](auth-migration.md) | The session model — the one large item, sequenced last and held back deliberately                      | 6 rows |

## Sequence

The waves exist because of real dependencies, not tidiness.

**Wave 1 — independent, and some of it urgent.**
`dead-code.md`, `security.md` Half A, `tooling.md`, `docs-hygiene.md`,
`seo.md`. Nothing here blocks on anything else. Two rows in it are live
production defects: the catch-all serving 500s, and an OG image that 404s on
every social share of every page.

**Wave 2 — blocked on Wave 1's tooling.**
`tokens.md` (needs stylelint and the `check` pipeline), `forms.md`,
`testing.md`.

**Wave 3 — blocked on tokens.**
`registry.md`. A registry component may name only tokens that exist, and
splitcart currently declares none of them.

**Wave 4 — unblocked, and the only wave still open.**
`auth-migration.md`. Its prerequisite was coverage of `users/`. That began with
`testing.md` and was finished by AU-0 on 2026-09-26: 238 tests where there were
none, and the anonymous-cart merge pinned at both doors through `reverse()`,
naming no serializer, so the migration cannot quietly change it. AU-0 also found
four defects that AU-3 now inherits, each held open by a strict `xfail` rather
than a note. AU-3 is the head of the chain. See that document for why the whole
thing is still last.

Waves 1 to 3 are closed. Their plans are listed above with their state.

## Three things worth knowing before reading further

**Django was API-only and did not know it.** `config/urls.py` ended in a
catch-all rendering a template that did not exist, from a `frontend/dist`
directory that did not exist, so every unrouted request returned 500 instead of
404 — dead code with a live effect. Removed 2026-09-25 along with
`ReactAppView`, `config/sitemaps.py` and the two `frontend/dist` settings
entries.

**`users/` had no tests, and closing that found a data leak.** The app owns
authentication, the `CartViewSet` including its cross-user permission
boundaries, and the money-adjacent cart optimisation. Writing the tests it now
has turned up Django's whole-site cache serving one shopper's cart, and one
account's email address, to whoever asked next. The middleware is gone and
`config/tests/test_caching.py` keeps it gone. Finishing the job in AU-0 turned
up four more: login and registration disagreeing about the spelling of the same
`anonymous_id`, a cart merge that is not atomic, and two `REST_AUTH` keys whose
absence means a password change neither proves you know the old password nor
ends any other session.

(The `CartViewSet` is described as nine-action in places. It is five `@action`s
plus the operations `SimpleRouter` generates; AU-0's record in
[`auth-migration.md`](auth-migration.md) counts them properly.)

**The backend is in better shape than everything around it.** Models, views and
serializers are already packages per concern. Test determinism is clean. No
scraping test contacts a real provider, and every HTTP call is patched at its
exact import path — the hard thing to get right. The gap is real but it is not
uniform, and the plans say so where it counts.

## Conformance

The ledger is
[`../../../freetheplatform/_docs/conformance/splitcart.md`](../../../freetheplatform/_docs/conformance/splitcart.md),
created by [`docs-hygiene.md`](docs-hygiene.md) DH-9. Verdicts there record what
landed, never what these plans intend. A rule whose preconditions do not exist
yet — FORMS-9/10/11, until the session model changes — is `n/a` with the reason,
not `fail` and not `pass`.
