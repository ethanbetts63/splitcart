# Convergence plan — testing

**Type:** status and work plan. Non-normative. The binding rules are
[`testing-standard-backend.md`](../../../freetheplatform/_docs/testing-standard-backend.md)
(TESTB-1..9) and
[`testing-standard-frontend.md`](../../../freetheplatform/_docs/testing-standard-frontend.md)
(TESTF-1..5).

Evidence: `scratchpad/gap-testing.md` (survey of 2026-09-25).

## The good news first

splitcart's backend is in better shape than the rest of this convergence
suggests. TESTB-8 largely holds already: `models/`, `views/` and `serializers/`
are packages per concern across the apps, not monoliths. TESTB-3 determinism is
clean, with one soft flag. TESTB-7 is **compliant** — no scraping test contacts
a real provider, and every `requests.get`/`post` is patched at its exact import
path, which is the harder thing to get right.

`factory_boy` and `Faker` are genuinely installed and used, so `_docs/TESTING.md`
is accurate on that point.

## The hole

**`users/` has no `tests/` directory at all.** Not a thin one — none.

That app owns authentication (`custom_login_serializer.py`,
`custom_register_serializer.py`), the entire `CartViewSet` — nine actions
including cross-user permission boundaries — and `utils/cart_optimization.py`,
the money-adjacent orchestration that feeds the (well-tested) `pipeline`
optimization algorithm.

TESTB-5 asks for failure-path coverage in proportion to risk. Auth and money
with zero coverage is the highest-severity finding in this entire sweep, and it
sits next to [`security.md`](security.md) SC-8's unvalidated `rename` action —
an unserialized write to a user-owned record, in the one app no test would
catch a regression in.

`users/views/cart_viewset.py` is also the largest file in the codebase at 246
lines across nine actions. Worth revisiting as a TESTB-8 borderline case once
tests exist to make splitting it safe.

## Work

| #    | Work                                                                                                                                                                                                             | Acceptance                                                                    |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| TS-1 | Restore a working test entry point. From a clean checkout, collection fails with `ImportError: No module named 'dotenv'` before reaching app code, and `./venv/Scripts/python` does not exist in this worktree. Document the real bootstrap in the README and make it work. | `pytest --collect-only` succeeds from a documented fresh setup.               |
| TS-2 | Add the root `conftest.py` that `_docs/TESTING.md` §4 already documents but which does not exist. Only `pipeline/tests/conftest.py` exists today. Model the fixture layer on freethedesk's: `drf_request_factory`, an `api_client`, and the half-built-DB guard. | The documented fixtures exist and are used.                                   |
| TS-3 | Create `users/tests/`, mirroring the app's package split. Cover: login and registration success and failure, `CartViewSet`'s nine actions including the cross-user permission boundary on each, and `cart_optimization`. Failure paths get weight proportional to risk (TESTB-5). | Every public unit in `users/` has a mirrored test module.                     |
| TS-4 | Add mirrored tests for `products/serializers/*` (4 files) and `pipeline/views/*` (10 files) — source is already split per concern, the tests just do not mirror it (TESTB-8).                                     | Each has a corresponding test module.                                         |
| TS-5 | Freeze the clock in `pipeline/tests/util_tests/test_product_reconciler.py:89-90`, which asserts against live `date.today()`.                                                                                     | No wall-clock dependence (TESTB-3).                                           |
| TS-6 | Add direct test files for the 4 of 6 scraper classes that have none. Keep the existing hand-built `Mock` approach rather than introducing `responses`/`vcrpy` — the current pattern already satisfies TESTB-7 and a new library is churn, not coverage. | Every scraper class has a test at the HTTP boundary.                          |
| TS-7 | Repair `requirements_dev.txt`: it is UTF-16LE with no `.in` source. Adopt the family's `pip-compile`-from-`.in` convention. Shared with [`security.md`](security.md) SC-9. | UTF-8, pinned, regenerable.                                                   |
| TS-8 | Build `npm run check` for the frontend. **This does not require a test runner.** Verified against both references: neither freethedesk nor allbikes uses vitest or jest — TESTF-2 is satisfied entirely by the static-plus-structural `check` pattern. splitcart simply has not built it. Composition is owned by [`tooling.md`](tooling.md) TL-10; this row is the TESTF-2 sign-off. | `npm run check` green before any change is called done.                       |
| TS-9 | Add the two structural checks that are buildable today (TESTF-3): a `check:sitemap` equivalent covering the 11 routes and two dynamic slug families against `app/sitemap.ts`, and a login/signup form-versus-serializer contract check. Token, OG-image and breadcrumb checks are blocked on [`tokens.md`](tokens.md) and [`seo.md`](seo.md) and arrive with those plans. | Both scripts exist, exit 0, and are in `npm run check`.                       |

## A correction to the repo's own claims

`CLAUDE.md` says "All 355+ tests should pass." A count of `def test_` across the
backend apps returns 1048. The figure is roughly three times stale in the
direction nobody checks. [`docs-hygiene.md`](docs-hygiene.md) removes the number
rather than updating it — a hardcoded test count is a fact that rots by
construction, and the suite itself is the place to read it from.
