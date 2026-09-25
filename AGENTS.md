# Agent instructions

## Repository role

`splitcart` is the SplitCart grocery price-comparison product
(https://www.splitcart.com.au/). It owns supermarket scraping, product and
price normalisation, cross-chain product matching, the cart-splitting
optimisation, and the public site.

The repository is a monorepo: a Django REST API at the root and a Next.js App
Router frontend under `frontend/`. The two deploy separately — the API to
PythonAnywhere at `api.splitcart.com.au`, the frontend to Vercel at
`www.splitcart.com.au`.

The sibling `../freetheplatform` repository holds reusable Django capabilities
and the canonical cross-project engineering policies. **splitcart consumes one
thing from it: `@freetheplatform/web-security`**, declared in
`frontend/package.json` and used by `next.config.ts` to build the response
header set. Nothing on the Python side — the `freetheplatform` distribution
appears in neither `requirements.txt` nor `requirements_dev.txt`, so the
session model, throttling and the §19 system checks are all still local.
Bringing splitcart onto those policies is in progress; see
[`_docs/convergence/README.md`](_docs/convergence/README.md) for what has and
has not landed, and
[`../freetheplatform/_docs/conformance/splitcart.md`](../freetheplatform/_docs/conformance/splitcart.md)
for the per-rule ledger.

## Read before changing

| Work                                                             | Required document                                                         |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Shared agent workflow or definition of done                      | `../freetheplatform/_docs/agent-workflow.md`                              |
| Any cross-project or reusable capability                         | `../freetheplatform/_docs/strategy.md`                                    |
| What of the shared standards splitcart has and has not adopted   | `_docs/convergence/README.md`                                             |
| The scrape → pipeline → database lifecycle                       | `_docs/pipeline.md`                                                       |
| Scraper behaviour end to end                                     | `_docs/scraping.md`                                                       |
| Testing a scraper, a cleaner or the normalisation chain          | `_docs/scraper_testing.md`                                                |
| Backend tests, fixtures, or pytest conventions                   | `_docs/TESTING.md`                                                        |
| Product identity matching (name/brand/size normalisation)        | `_docs/normalized_name_brand_size.md`                                     |
| The `ProductBrand` model and brand reconciliation                | `_docs/product_brand.md`                                                  |
| Cart-splitting optimisation                                      | `_docs/optimization.md`                                                   |
| Substitute matching and ranking                                  | `_docs/substitutions.md`                                                  |
| Bargain detection and scoring                                    | `_docs/bargains.md`, `_docs/bargain_stats.md`                             |
| `ProductPriceSummary` pre-computed aggregates                    | `_docs/product_price_summary.md`                                          |
| The product category hierarchy and primary categories            | `_docs/categories.md`                                                     |
| `companies` app (Company, categories, pillar pages)              | `companies/README.md`                                                     |
| `products` app (Product, Price, substitutions, the public API)   | `products/README.md`                                                      |
| `pipeline` app (ingest, generate, reconcile)                     | `pipeline/README.md`, `pipeline/management/commands/README.md`            |
| `users` app (auth, carts, the optimisation entry point)          | `users/README.md`                                                         |
| Files under `frontend/`                                          | `frontend/AGENTS.md` in addition to this file                             |
| Frontend styling, Tailwind, CSS, lint, or breakpoints            | `../freetheplatform/_docs/lint-rules.md`                                  |
| Design tokens                                                    | `../freetheplatform/_docs/token-contract.md`                              |
| Any form (new, edited, or converted)                             | `../freetheplatform/_docs/forms-standard.md`                              |
| Security, authentication, sessions, headers, or input            | `../freetheplatform/_docs/security-standard.md`                           |
| Metadata, structured data, sitemap, robots, or indexation policy | `../freetheplatform/_docs/seo-standard.md` — read its sourcing rule first |

Read only the documents relevant to the issue; do not load the whole `_docs`
directory.

## Boundaries

- Scraping targets, normalisation heuristics, the optimisation algorithm, the
  category taxonomy, and SplitCart wording stay local.
- `@freetheplatform/web-security` is the only shared capability in use, and it
  arrived with the header work recorded in
  [`_docs/convergence/security.md`](_docs/convergence/security.md). Adding any
  further `freetheplatform` (PyPI/git) or `@freetheplatform/*` (npm) dependency
  applies the tests in `../freetheplatform/_docs/strategy.md` first, and records
  the decision. A pinned tag, never a branch: two deploys of one lockfile must
  not install different code.
- Scraping runs locally; database writes run on the server. A management
  command that reads an inbox and writes to the database is server-side, and
  `generate --subs` cannot run on the server at all because its ML
  dependencies are only in `requirements_dev.txt`. `_docs/pipeline.md` is the
  authority on which half a command belongs to.
- Treat URLs, migrations, the `normalized_name_brand_size` key, the archived
  JSONL under `pipeline/data/archive/`, and the internal-API contract between
  the local machine and the server as compatibility surfaces.
- Removing a subsystem means removing its documentation in the same commit.
  Store grouping, IGA support and the GS1 prefix system were all taken out of
  the code and left behind in the prose for months; that is what half the
  stale claims in `_docs/` were.
- Preserve unrelated worktree changes. Do not reset, overwrite, or broadly
  reformat files outside the issue.
- Never create a branch, and never switch, rebase, or reset to escape a
  mistake. Work commits straight onto the existing long-lived branch. A large
  change lands as a sequence of coherent commits, not as a side channel. See
  [`../freetheplatform/_docs/agent-workflow.md`](../freetheplatform/_docs/agent-workflow.md#branching).

## Verification

There is no CI in this repository. Nothing runs these for you; the agent that
changed the area runs them.

| Changed area              | Commands from repository root                                                                                   |
| ------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Django/Python             | `./venv/Scripts/python -m pytest <relevant paths>`; broaden to `./venv/Scripts/python -m pytest` when warranted |
| Django models             | `./venv/Scripts/python manage.py makemigrations --check --dry-run` plus relevant tests                          |
| Frontend static checks    | `cd frontend; npm run check`                                                                                    |
| Frontend production build | `cd frontend; npm run build`                                                                                    |
| Documentation only        | Link and path checks against the repository, Prettier for changed Markdown, and `git diff --check`              |

A commit-time subset of the above is available:
`git config core.hooksPath .githooks`, once per clone. See
[`README.md`](README.md#the-commit-hook).

## Definition of done

See the shared criteria in
[`../freetheplatform/_docs/agent-workflow.md`](../freetheplatform/_docs/agent-workflow.md#definition-of-done).
Locally that means: implemented behaviour matches the owning app `README.md`
and any `_docs/` reference; obsolete code and documentation in the changed
scope are removed; and no intra-repo documentation link is left dangling.
