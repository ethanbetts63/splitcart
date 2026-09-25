# Convergence plan — design tokens and CSS

**Type:** status and work plan. Non-normative. The binding rules are
[`token-contract.md`](../../../freetheplatform/_docs/token-contract.md)
(TOKEN-1..11) and [`lint-rules.md`](../../../freetheplatform/_docs/lint-rules.md)
(LINT-1..11).

## Where splitcart is

TK-1 through TK-13 landed on 2026-09-25. `frontend/src/styles/tokens.css`
declares the shared semantic families, the nine type rungs at the shared
values, and the `--focus-ring` / `--ring-field` pair; the 232 palette
utilities, the 174 fixed type sizes, the twelve template-literal class
strings and the five undeclared-token reads are gone; and `npm run check`
runs `lint`, `lint:css`, `check:tokens` and `check:text-scale` green with the
shared design-system ESLint block switched on.

TK-14 landed the same day, in the shared repo rather than here: `FAMILY` in
`freetheplatform/frontend/lint/token-drift.mjs` now names splitcart, so
`check:tokens` in any of the four repos resolves and compares all four
ladders. They agreed on the first run, character for character.

| Check              | Result                                            |
| ------------------ | ------------------------------------------------- |
| `lint`             | 0 errors, 0 warnings, design-system rules enabled |
| `lint:css`         | clean (was 125 errors)                            |
| `check:tokens`     | exit 0                                            |
| `check:text-scale` | exit 0, nine rungs, generated not hand-written    |
| `build`            | 23 routes                                         |

## Work still open

| #     | Work                                                                                                                                                                                                                                                                                                                                                                                                                                 | Acceptance                                                        |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------- |
| TK-15 | Declare the rest of the `--space-*` ramp. Only `--spacing-section` exists today, deliberately: the `--spacing-*` namespace silently overrides Tailwind's container scale, and splitcart still sizes panels with `max-w-lg`, `max-w-2xl`, `max-w-3xl` and `max-w-5xl`. Those call sites move to a role-named `--container-*` scale first; then the space rungs can arrive. `scripts/check-tokens.mjs` already fails on the collision. | `gap-m` and `p-l` exist, and no width class names a spacing rung. |

## Judgement calls this conversion made

Recorded because they are not re-derivable from the diff.

- **The supermarkets are a `--category-*` set, named rather than numbered.**
  Woolworths green, Coles red and Aldi blue are three real brands' own
  colours on every price-comparison bar. allbikes numbers its categorical set
  because its categories are internal enum values; here "which one is
  `--category-2`" has no answer anybody would remember.
- **Three feedback values moved, and only these three.** `--fill-success` was
  `green-500` carrying white text at 2.3:1; `--text-success` was `green-600`
  at 3.0:1 on white, used on a 0.75rem chip; `--text-danger` was `red-500` at
  3.7:1. All three failed WCAG AA at the contrast their call sites used them
  at. Everything else in the file is the value the site already rendered.
- **`--link`/`--link-hover` and `--shadow-s` arrived for the registry, not for
  a redesign.** The shared `button.tsx` names `text-link`/`hover:text-link-hover`
  and the shared `select.tsx` names `shadow-s`, so adopting them (registry.md
  RG-7) needed all three declared here. `--link` is `var(--text-action)` rather
  than a second blue: one value, two names, so a rebrand cannot separate them.
  `--link-hover` is `--neutral-900` (17.7:1) rather than a darker blue, matching
  the step `--border-strong-hover` already takes. `--shadow-s` is Tailwind's
  stock `shadow-md` geometry over the neutral ramp, which is what the select
  popover already drew, so naming it changed nothing on screen.
- **`--focus-ring` is `--brand-700`, not the brand yellow.** A focus indicator
  has to clear 3:1 against what is behind it; `#fde047` on white is 1.3:1.
- **`warning` and `info` are declared with no consumer.** The quad is the point
  of the family: the fifth meaning should arrive as a token rather than as the
  first raw amber somebody reaches for. Their values are allbikes'.
- **`.site-shell` is a single fluid cap, not Tailwind's five `container`
  steps.** Content is wider between breakpoints than it was and narrower above
  1536px. That is the shape both sibling repos use and the reason the rail
  exists, but it is the largest visual change in the conversion.

## Adjacent things this conversion found and did not fix

- Six `components/common/*` primitives have no importer anywhere:
  `breadcrumb`, `input-otp`, `navigation-menu`, `slider`, `toggle`,
  `toggle-group`. This was nine; `alert`, `checkbox` and `table` were the three
  the registry also ships, and [`registry.md`](registry.md) resolved them on
  2026-09-25 by deleting them here and scoping them away in `sync.mjs` rather
  than adopting a copy nothing calls. The remaining six are not registry files,
  so nothing upstream is waiting on them — they are
  [`dead-code.md`](dead-code.md)'s to remove.
- `scrollbar-hide` is used in two components and generates nothing:
  `tailwind-scrollbar-hide` is a dependency but `@plugin` never registers it.
  Adding the plugin would change how those two carousels look, so it is a
  decision rather than a fix.
- `next-themes` is still a dependency, and the only thing that reads it is
  `sonner.tsx`'s `useTheme()`, which has no provider above it. The `.dark`
  block and the `dark:` variants are gone; the dependency is
  [`dead-code.md`](dead-code.md)'s to remove.
