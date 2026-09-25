# Convergence plan — design tokens and CSS

**Type:** status and work plan. Non-normative. The binding rules are
[`token-contract.md`](../../../freetheplatform/_docs/token-contract.md)
(TOKEN-1..11) and [`lint-rules.md`](../../../freetheplatform/_docs/lint-rules.md)
(LINT-1..11).

Evidence: `scratchpad/gap-tokens.md` (survey of 2026-09-25).

## Where splitcart actually is

`frontend/src/index.css` is unmodified `shadcn init` output. Stock
`--primary` / `--muted` / `--card` / `--sidebar` / `--chart-N` names backed by
raw `oklch()` literals, and no `styles/tokens.css` at all.

None of the required semantic families exist: no `--surface-*`, no `--text-*`
role family, no `--fill-*`, no decorative `--accent-*`, no feedback quad
(`--destructive` exists, unsplit), no `--focus-ring` / `--ring-field`, and none
of the nine text rungs — which do not exist as utilities either.

This is the plan's central fact: splitcart is not drifting from the token
contract, it has never been on it. Nothing here is a "fix a few call sites" job.

## The measured surface

| Symptom                                                                       | Scale                                                           |
| ----------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Stock Tailwind palette utilities (`bg-gray-500`) outside `components/ui/`     | 232 occurrences across 27 files                                  |
| Worst files                                                                   | `ResultsDisplay.tsx` (46), `SubstitutionPage.tsx` (28), `CartItemTile.tsx` (24) |
| Non-rung text sizes (`text-xs`..`text-7xl`)                                   | 174 call sites across 29 files                                   |
| Arbitrary bracket values outside `components/ui/`                             | 13                                                               |
| Template-literal dynamic classes, none using `cn()`                           | 12 sites                                                         |
| Distinct focus-ring spellings in the shadcn primitives alone                  | at least 5                                                       |

**One live bug sits inside this gap.** `FaqSection.tsx:28,32,36,37,40` reads
`var(--text-light-primary)` and four siblings — tokens that are declared
nowhere in the repo. They resolve to nothing today. TOKEN-8 forbids reading an
undeclared token, and here the rule is not a formality: the component is
rendering with no colour at those five sites.

## Sequence

The order matters. Every sweep row depends on the vocabulary existing first.

| #    | Work                                                                                                                                                                                                                                       | Acceptance                                                                               |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| TK-1 | Delete `src/App.css`. Confirmed dead Vite template scaffolding — zero importers, and its contents are the React logo spin animation.                                                                                                       | File gone; nothing references it.                                                        |
| TK-2 | Create `src/styles/tokens.css` declaring the full semantic vocabulary, with palette ramps private to that file (TOKEN-1). Take the names and the resolved values from freethedesk and allbikes so all repos agree — do not invent a third spelling (TOKEN-2, TOKEN-6). | Every `--surface-*`, `--text-*`, `--border-*`, `--fill-*`, `--action-primary`, `--accent-*` and the danger/warning/success/info quad is declared once. |
| TK-3 | Map the shadcn tokens onto the semantic ones and retire the shadcn names: `--background`→`--surface-page`, `--foreground`→`--text-primary`, `--muted`→`--surface-muted` and `--text-muted`, `--destructive`→ the danger quad's surface/border/fill/text. Resolve the `--accent` name collision deliberately: shadcn's `--accent` is a hover/selected surface, the contract's `--accent-*` is decorative and never a second action colour (TOKEN-3). They are different roles that share a spelling — rename, do not alias. | No component names a shadcn-era token.                                                   |
| TK-4 | Decide the orphans. `--color1` has no consumer — delete it. The seven `--sidebar-*` and five `--chart-*` tokens have no reference-repo equivalent: keep only those with a real consumer, and declare the survivors as proper roles in the token file rather than as a shadcn block. | Every token in the file has a named consumer or is gone.                                 |
| TK-5 | Declare the nine text rungs and generate `text-sizes.generated.ts` from `tokens.css` via a `sync-text-scale.mjs` adapted from freethedesk. Wire `check:text-scale` (TOKEN-7, LINT-6). Rungs stay monotonic and gap-free at both ends of each clamp (TOKEN-10). | `npm run check:text-scale` exits 0 and the generated file is derived, never hand-written. |
| TK-6 | Replace bare `twMerge()` in `lib/utils.ts:4` with `extendTailwindMerge()` registering the custom `text-*` rungs. Today `cn()` exists but registers nothing, so a rung utility and a stock size utility do not deduplicate.                  | `cn('text-body', 'text-lead')` resolves to one class.                                    |
| TK-7 | Add `lib/controlState.ts` with the three named focus treatments, and define `--focus-ring` (outline) and `--ring-field` (box-shadow) as the only two draw methods (TOKEN-4, REG-7). Retrofit the primitives. Two of them — `input.tsx:11` and `navigation-menu.tsx:94` — currently render **no focus indicator at all**; that is an accessibility defect, not a style preference. | One outline treatment and one box-shadow treatment; no hand-written focus CSS; every interactive element has a visible focus state. |
| TK-8 | Add `check:tokens` (adapted from freethedesk) asserting no stylesheet reads an undeclared token and `--spacing-*` never shadows the container scale (TOKEN-8). This is what would have caught the `FaqSection` bug.                        | `npm run check:tokens` exits 0.                                                          |
| TK-9 | Sweep the 232 palette utilities across 27 files onto semantic tokens. Heaviest three files first — they are a third of the total. Fix the five undefined `--text-light-primary` reads in `FaqSection.tsx` as part of this.                  | `lint:css` and `check:tokens` clean; no stock palette utility outside an approved exception. |
| TK-10 | Sweep the 174 non-rung text sizes across 29 files onto the nine rungs. Choose an existing rung before adding one; a repeated value extends the scale in `tokens.css`, never as a literal at a call site (TOKEN-9).                         | No `text-xs`..`text-7xl` outside an approved exception.                                  |
| TK-11 | Convert the 12 template-literal dynamic class sites to complete-string maps (LINT-7) and route every conditional class through `cn()`. `companyColorMap` in `PriceComparisonChart.tsx:13` is already the correct pattern — copy its shape. | No class name assembled by fragment concatenation.                                       |
| TK-12 | Give splitcart's own components typed CVA variants instead of copied class bundles (LINT-3). CVA is currently used only in the eight shadcn-generated files and never adopted for splitcart's own. Variants are semantic (`danger`), never palette (`red`). | Reusable states are components with typed variants.                                      |
| TK-13 | Import the shared lint rule definitions from `freetheplatform/frontend/lint/` rather than restating them (LINT-10). `eslint.config.js` imports none of them today.                                                                         | The design-system rules are imported, not copied.                                        |

## Judgement calls this plan makes

- **`components/ui/` is swept, not exempted.** LINT-4 is explicit that no
  directory is exempt because of its origin. Stock shadcn output is still code
  in this repo. The 232-occurrence count deliberately excludes it only because
  [`registry.md`](registry.md) may replace twelve of those files outright —
  sequence TK-9 after that decision lands, then sweep whatever remains.
- **TK-9 and TK-10 overlap heavily** (both are dominated by the same ~27 files).
  Do them file-by-file together, not as two passes over the same tree.
- **`index.css` stays** as the foundation entry point importing
  `styles/tokens.css`; it is a foundation under LINT-8, not an exception. The
  one `.no-spinner` component class currently sitting in it is misplaced and
  moves to its consumer.
