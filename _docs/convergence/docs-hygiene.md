# Convergence plan — documentation and repo hygiene

**Type:** status and work plan. Non-normative. The binding rules are
[`agent-workflow.md`](../../../freetheplatform/_docs/agent-workflow.md) and the
ownership rule in
[`freetheplatform/_docs/README.md`](../../../freetheplatform/_docs/README.md).

Evidence: `scratchpad/gap-docs.md` (survey of 2026-09-25).

## What is wrong

splitcart's documentation describes a different application than the one in the
repository. The Vite-to-Next migration landed in the source and never reached
the prose, so the two most-read files — `README.md` and `CLAUDE.md` — are
actively misleading. `CLAUDE.md` instructs every agent to read `README.md`
first, which means the wrong stack is the first thing anyone learns.

There is also no `AGENTS.md`. Every conforming repo in the family routes agents
to the right document by issue type; splitcart routes them nowhere.

## Factual errors to correct

| Claim                                                                    | Fact                                                                                          |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| Frontend is "React / TypeScript (Vite)", React Router, React Context     | Next.js 16 App Router — `next.config.ts`, `src/app/`, `app/sitemap.ts`, `app/robots.ts`. `package.json` contains neither vite nor react-router. |
| Setup uses `reset_splitcart.ps1`                                         | The file is `reset_django_project_robust.ps1`.                                                |
| Settings live in a `splitcart/` package                                  | They live in `config/`. `manage.py`, `wsgi.py` and `asgi.py` all point at `config.settings`; no `splitcart/` package exists. |
| "All 355+ tests should pass"                                             | `def test_` across the backend counts 1048. Remove the number rather than updating it — a hardcoded count rots by construction. |
| `.env` needs `PORT=3306`                                                 | `settings.py` reads `DB_PORT`.                                                                |
| `./venv/Scripts/python -m pytest`                                        | Correct — matches the repo's own venv instructions. Not an error. Keep it.                    |

## Broken links

Six intra-repo documentation links point at files that do not exist:

- `README.md` → `_docs/gs1.md`, `_docs/home.md`, `_docs/scraper_testing.md`,
  `_docs/store_grouping.md`
- `README.md` → `scraping/README.md`
- `pipeline/README.md` → `database_updating_classes/product_updating/README.md`

Two of those four missing `_docs` files are the ones README calls "the two most
interesting pieces of engineering in this codebase". Either write them or stop
advertising them; a reader who follows that pointer and lands on a 404 learns
something worse than nothing.

Per-app `README.md` files for `companies/`, `products/`, `pipeline/` and
`users/` all check out clean — named classes, modules and commands exist. Leave
them alone.

## Work

| #    | Work                                                                                                                                                                                       | Acceptance                                                              |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| DH-1 | Write the root `AGENTS.md`, modelled on freethedesk's: a read-before-changing routing table covering splitcart's real apps and real documents, the boundaries section, the verification table, and the definition-of-done pointer. Route frontend work to a new `frontend/AGENTS.md`. State the branching rule — work commits straight onto the existing long-lived branch, never a feature branch. | Both files exist and every document they name exists.                   |
| DH-2 | Rewrite `README.md` against the actual stack. Fix every row in the table above. Keep the project's voice and the genuinely good parts — the "two most interesting pieces of engineering" framing is worth keeping once the links resolve. | No factual error survives; every link resolves.                         |
| DH-3 | Update `CLAUDE.md`: correct the structure diagram (`config/`, not `splitcart/`), drop the stale test count, fix the "(Vite)" label.                                                        | Accurate.                                                               |
| DH-4 | Fix or remove the six broken links. For the four missing `_docs` files, prefer writing the two the README headlines (`store_grouping.md`, `scraper_testing.md`) and removing the pointers to the other two if nothing is there to document. | Zero broken intra-repo links.                                           |
| DH-5 | Replace `frontend/README.md` — it is still the unedited Vite scaffold README.                                                                                                              | Describes the Next.js app.                                              |
| DH-6 | Add `.gitattributes`, `.githooks/` and `.prettierrc` from freethedesk.                                                                                                                     | Present and matching.                                                   |
| DH-7 | Untrack `node_modules/.package-lock.json`. It is the only tracked artefact in the repo; everything else the `.gitignore` scopes is genuinely untracked, so the ignore file is otherwise doing its job. | `git ls-files` shows no build or dependency artefact.                   |
| DH-8 | Delete the three `deprecated_*` documents. Owned by [`dead-code.md`](dead-code.md) DC-10; listed here so the docs picture is complete in one place.                                        | Gone.                                                                   |
| DH-9 | Create `freetheplatform/_docs/conformance/splitcart.md` with a row per rule across all eight standards, and add splitcart to the family lists in `freetheplatform/_docs/README.md`. Verdicts are filled from what actually landed — not from what this plan intends. | The ledger exists and every verdict is evidenced.                       |

## The strategy boundary

splitcart depends on neither the `freetheplatform` Python package nor any
`@freetheplatform/*` npm package. It is entirely outside the shared-package
graph, and that is the root of several gaps in the other plans rather than a
separate problem.

Verdicts on each shared capability, applying strategy.md's tests:

| Capability                      | Verdict       | Reason                                                                                      |
| ------------------------------- | ------------- | ------------------------------------------------------------------------------------------- |
| `web-security` CSP + sanitiser  | **adopt now** | splitcart emits no CSP at all. Cheapest real security win available.                        |
| Security bounds table           | **adopt now** | Closes a live blind spot; see [`forms.md`](forms.md) FM-4.                                  |
| Auth / cookie-JWT sessions      | adopt later   | Large migration with a live blast radius — [`auth-migration.md`](auth-migration.md).        |
| Component registry              | adopt later   | Blocked on tokens — [`registry.md`](registry.md).                                           |
| Messaging / email               | stays local   | No shared need demonstrated.                                                                |
| Search Console reporting        | adopt later   | No measurement plumbing here yet.                                                           |
