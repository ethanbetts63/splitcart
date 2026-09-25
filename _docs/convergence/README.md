# Convergence — splitcart

**Type:** migration tracking. Non-normative. The binding policies live in
[`../../../freetheplatform/_docs/`](../../../freetheplatform/_docs/README.md)
and are never restated here.

This directory is the single record of bringing splitcart onto the shared
engineering policies that already govern allbikes, bloomprint and freethedesk.
It is a to-do list with evidence attached. Delete a row when it lands; delete a
plan when its rows are gone; delete this directory when there is nothing left.

Surveyed 2026-09-25 against the standards as they stood that day.

## The one-paragraph summary

splitcart was never on these policies — it is not drifting from them. It sat
outside the shared-package graph entirely until 2026-09-25, when the header work
brought in `@freetheplatform/web-security`; the Python side is still untouched,
so that is one npm package rather than a shared session model. Its
frontend completed a Vite-to-Next migration that never reached its
documentation, its configuration, or its dead routes. Its design tokens are
unmodified `shadcn init` output. It has no formatter, no CSS lint, no structural
checks, no `AGENTS.md`, and no tests for the app that owns authentication and
carts.

None of that is unusual for a repo brought in late, and most of it is cheap.

## The plans

| Plan                                     | Owns                                                                                                   |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| [`dead-code.md`](dead-code.md)           | Vite-era residue, including a catch-all route that turns 404s into 500s                                |
| [`security.md`](security.md)             | Configuration and boundary defects — admin exposure, transport settings, throttles, unvalidated writes |
| [`tooling.md`](tooling.md)               | Prettier, stylelint, eslint, tsconfig, the dependency baseline, `npm run check`                        |
| [`docs-hygiene.md`](docs-hygiene.md)     | `AGENTS.md`, the factually wrong README, broken links, the conformance ledger                          |
| [`seo.md`](seo.md)                       | The page registry, sitemap, robots, and four uncoordinated JSON-LD emitters                            |
| [`tokens.md`](tokens.md)                 | The semantic token vocabulary, the nine text rungs, and the sweep onto them                            |
| [`testing.md`](testing.md)               | The missing `users/` test suite and the frontend check pipeline                                        |
| [`forms.md`](forms.md)                   | Three forms, their schemas, and the field bounds table                                                 |
| [`registry.md`](registry.md)             | Becoming a registry consumer, gated on tokens                                                          |
| [`auth-migration.md`](auth-migration.md) | The session model — the one large item, sequenced last and held back deliberately                      |

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

**Wave 4 — blocked on tests, which have now landed.**
`auth-migration.md`. Its prerequisite was coverage of `users/`, and that
arrived with `testing.md`: 171 tests where there were none, and the
anonymous-cart merge pinned independently of the serializer the migration
deletes. See that document for why it is still last.

## Three things worth knowing before reading further

**Django is API-only, and does not know it.** `config/urls.py` ends in a
catch-all rendering a template that does not exist, from a `frontend/dist`
directory that does not exist. Every unrouted request returns 500 instead of 404. This is dead code with a live effect.

**`users/` had no tests, and closing that found a data leak.** The app owns
authentication, the nine-action `CartViewSet` including its cross-user
permission boundaries, and the money-adjacent cart optimisation. Writing the
171 tests it now has turned up Django's whole-site cache serving one shopper's
cart, and one account's email address, to whoever asked next.

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
