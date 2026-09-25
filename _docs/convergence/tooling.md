# Convergence plan — frontend tooling and baseline

**Type:** status and work plan. Non-normative. The binding rules are
[`frontend-baseline.md`](../../../freetheplatform/_docs/frontend-baseline.md)
(BASE-1..5) and [`lint-rules.md`](../../../freetheplatform/_docs/lint-rules.md)
LINT-2/4/9/10.

Evidence: `scratchpad/gap-tooling.md` (survey of 2026-09-25).

## The precondition

`frontend/registry/tooling/baseline/baseline-drift.mjs` in freetheplatform
hardcodes `CONSUMERS = ['allbikes', 'bloomprint', 'freethedesk']`, and
`sync.mjs` does the same. splitcart is not a family member in either. Until it
is added there, `check:baseline` in this repo reports on a family it is not part
of and means nothing.

That edit belongs in freetheplatform, not here — shared tooling is owned by the
shared repo. It is the first row of this plan because every other baseline row
depends on it.

## Measured starting point (2026-09-25)

| Check        | Result                                              |
| ------------ | --------------------------------------------------- |
| `typecheck`  | clean                                               |
| `lint`       | 47 errors, 2 warnings — mostly `no-explicit-any`    |
| `format`     | no formatter configured                             |
| `lint:css`   | no stylelint configured                             |
| `check`      | script does not exist                               |

`lint` being red is the honest baseline. Do not treat "green" as the starting
state anywhere in this plan.

## Work

| #    | Work                                                                                                                                                                                                              | Acceptance                                                                                |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| TL-1 | Add `splitcart` to `CONSUMERS` in `freetheplatform/frontend/registry/tooling/baseline/baseline-drift.mjs`. Same commit adds it to `sync.mjs`'s consumer list (see [`registry.md`](registry.md)).                  | `baseline-drift.mjs --report` includes a splitcart column.                                |
| TL-2 | Migrate `eslint.config.js` → `eslint.config.mjs`, modelled on freethedesk's. It is unmigrated Vite scaffold: no `eslint-config-next` at all (so no Core Web Vitals or Next rules), ignores `dist` instead of `.next`, stale `ecmaVersion: 2020`. Add `eslint-config-next`. Narrow the `lint` script from `eslint .` to `eslint src`. | `next lint` rules are active; the config file matches the references' shape.              |
| TL-3 | Clear the 47 existing lint errors. They are overwhelmingly `no-explicit-any` in `services/`, `types/` and `context/`. Type them properly — do not silence the rule. LINT-9 forbids buying green with a broad ignore. | `npm run lint` exits 0 with no new suppressions.                                          |
| TL-4 | Add `prettier` + `.prettierrc.json` + `.prettierignore`, copied from freethedesk. Add `format` and `format:check` scripts. Run `format` once as its own commit so the reformat does not contaminate later diffs.   | `npm run format:check` exits 0.                                                           |
| TL-5 | Add `stylelint`, `stylelint-config-standard`, `stylelint-declaration-strict-value` and `.stylelintrc.mjs` from freethedesk. Add the `lint:css` script.                                                            | `npm run lint:css` runs. It will be red until [`tokens.md`](tokens.md) lands — that is expected and belongs to that plan. |
| TL-6 | Level `tsconfig.json` to the references: `target` ES2017 → ES2022, `allowJs` → true, add `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`, `verbatimModuleSyntax`, add `**/*.mts` to `include`. | `npm run typecheck` still clean after the stricter options, or the newly surfaced errors are fixed, not disabled. |
| TL-7 | Exact-pin every package on the baseline PINNED list. splitcart carets or tildes all of them (`@vercel/analytics ^2.0.1`, `class-variance-authority ^0.7.1`, `clsx ^2.1.1`, `typescript ~5.9.3`). BASE-5.          | No PINNED package carries a range operator.                                               |
| TL-8 | Resolve the `lucide-react` skew: splitcart is on `^0.545.0`, allbikes on `1.14.0` — a full major behind, and outside the scoped repo list. Level it and extend the scoped row to include splitcart. Note that v1 kept the old icon names as aliases, so this landed in bloomprint with no source changes. | `check:baseline` reports lucide-react agreeing across every repo that has it.             |
| TL-9 | Add scoped baseline rows for the Radix primitives already shared with allbikes: `@radix-ui/react-checkbox`, `-dialog`, `-label`, `-select`, `-slot`, `-switch`. They are a two-repo dependency with no row — the exact shape of the documented lucide-react incident. Leave `@tanstack/react-query`, `sonner`, `next-themes`, `input-otp`, `tailwind-scrollbar-hide` unscoped: genuinely splitcart-only today, and BASE-4 says a row arrives when a second repo adopts one, not before. | The six Radix packages are scoped rows; the five single-repo packages are deliberately absent and this file says why. |
| TL-10 | Compose `npm run check`. Start with what exists — `format:check`, `lint`, `lint:css`, `typecheck`, `check:baseline` — and let the other plans append their `check:*` scripts as they land. TESTF-2.                | `npm run check` exists and runs every configured check in sequence.                       |

## Deliberately not here

- The `check:*` structural scripts for SEO, forms and tokens are specified in
  their own plans. This plan owns only the `check` composition they append to.
- `@freetheplatform/web-security` is a PINNED package splitcart lacks, but
  adding it is a dependency decision that belongs to
  [`auth-migration.md`](auth-migration.md), not a tooling row.
- `zod` and `marked` are likewise PINNED-but-absent. `zod` arrives with
  [`forms.md`](forms.md); `marked` has no consumer here and should stay absent.
