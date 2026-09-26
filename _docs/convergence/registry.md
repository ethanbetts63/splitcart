# Convergence plan — component registry

**Type:** status and work plan. Non-normative. The binding rules are
[`component-registry.md`](../../../freetheplatform/_docs/component-registry.md)
(REG-1..7).

## Status: eleven files

splitcart joined `CONSUMERS` in
`freetheplatform/frontend/registry/scripts/sync.mjs` on 2026-09-25 and takes
eleven files, each carrying the `/* Component registry: … */` banner and held
byte-identical by `sync.mjs --check`:

| File                                      | What it brought                                            |
| ----------------------------------------- | ---------------------------------------------------------- |
| `lib/utils.ts`                            | `cn()` taught the nine type rungs, maintained in one place |
| `lib/controlState.ts`                     | The three focus treatments and the two disabled reasons    |
| `types/FaqItem.ts`                        | The FAQ item, with its optional in-answer links            |
| `components/seo/StructuredDataScript.tsx` | The JSON-LD emitter that escapes `<`                       |
| `components/common/badge.tsx`             | The chip, and the focus ring a badge-as-link needs         |
| `components/common/button.tsx`            | Six variants, six sizes, the two disabled reasons          |
| `components/common/card.tsx`              | The panel and its six slots                                |
| `components/common/input.tsx`             | The text field, with the iOS 16px zoom floor               |
| `components/common/label.tsx`             | The field label, disabled with its group                   |
| `components/common/select.tsx`            | The listbox, its popover and its item indicator            |
| `components/common/spinner.tsx`           | The one busy indicator                                     |

Everything else in the registry has a `SCOPED` row in `sync.mjs` giving the
reason it would be dead code here today (REG-5). Those reasons are the record
of how splitcart differs; read them there rather than restating them.

Two things this made true that are worth knowing:

- `lib/utils.ts` had to be split first. The registry's version is `cn()` and
  nothing else. `getCsrfToken`/`getAuthHeaders` are now `lib/authHeaders.ts`
  and `debounce` is `lib/debounce.ts`.
- `lib/schema.tsx` is gone. It was a one-line forward kept alive only by the
  five route files that imported `@/lib/schema`; those now import
  `@/components/seo/StructuredDataScript` directly (2026-09-25). There is still
  exactly one emitter, and now only one path to it.

## Work still open

| #     | Work                                                                                                                                         | Blocked on                                                   |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| RG-11 | Adopt `marketing/FaqSection.tsx`, `marketing/renderFaqAnswer.tsx` and `common/eyebrow.tsx`, replacing the local `components/FaqSection.tsx`. | A `font-weight-*` ramp; `tokens.md` TK-15 cleared 2026-09-26 |

### What RG-7 and RG-9 cost, kept so they are not re-litigated

RG-9 moved `src/components/ui/` to `src/components/common/` and RG-7 reconciled
the primitives inside it. Both landed on 2026-09-25.

**The move was a rename here rather than an option in `sync.mjs`.** The obvious
alternative was a per-repo destination override — land `components/common/*` at
`components/ui/*` for splitcart alone. `sync.mjs` is a literal file copy with no
path rewriting, and that is load-bearing rather than incidental: registry files
import each other by absolute alias, `@/components/common/eyebrow` and
`@/components/seo/StructuredDataScript` among them. An override would have to
rewrite import specifiers as well as destinations, which turns a byte copy into
a transform and takes REG-1's drift check from a plain `diff` to a comparison
that has to know what the transform was. That is a permanent cost on tooling
three other repositories depend on, paid to avoid a one-off rename in the repo
that was out of step. Twenty-five files imported from `ui/` in four spellings
(`@/components/ui/x`, `./ui/x`, `../components/ui/x`, `../../components/ui/x`)
and all twenty-five moved in one commit.

**Four files did not follow the family into `common/`.** `login-form.tsx`,
`signup-form.tsx` and the two `*.schema.ts` beside them are splitcart's own
forms, not shadcn primitives; they went to `src/components/forms/`, which is the
directory convention `components/seo/` already set here and which the two form
checks now name. (`settings-dialog.tsx`, which an earlier draft of RG-9 listed
with them, was never in `ui/` — it has always sat at `src/components/`.)

**The reconciliation went the registry's way almost everywhere.** All ten local
primitives had diverged, 170 lines in total, and nearly all of it was splitcart
sitting on an older shadcn baseline: the banner and the `@/lib/*` aliases, the
iOS 16px font floor on `input` and `select`, `disabledUnavailableClassName` in
place of hand-spelled `disabled:` classes, `aria-invalid:ring-fill-danger/20`,
`border-border-strong` over `border-border-default`. Two hunks went the other
way and were pushed upstream rather than kept as a fork:

- **`text-on-dark`, not `text-on-brand`, on the danger fill** (`button.tsx` and
  `badge.tsx`). The two tokens are the same white in allbikes and bloomprint, so
  the upstream edit changed nothing there — but splitcart's brand is yellow, so
  its `--text-on-brand` is black, and black on `--fill-danger` is 4.3:1. The
  cart-count badge is the destructive variant at 0.72rem: a WCAG AA failure the
  byte-copy would have shipped. White is 4.8:1.
- **`focusRingClassName` on `badge.tsx`.** A badge carries `[a&]:hover:`
  variants, so it renders as an anchor; a focusable anchor with no focus
  treatment falls back to the browser's ring, which is the defect REG-7 exists
  to stop. Inert on a `<span>`, so nothing moved in the other two repos either.

**Three tokens landed first**, all named by the registry's copies and none
declared here: `--link` and `--link-hover` for `button.tsx`'s `link` variant,
and `--shadow-s` for `select.tsx`'s popover. See [`tokens.md`](tokens.md) for
the values and the contrast ratios.

**Four of the eleven are still scoped away, and not aspirationally.** `alert`,
`checkbox`, `table` and `textarea` have no caller in splitcart — the first three
had sat unimported in `ui/` as `shadcn add` output and were deleted with the
move, and `textarea` never existed here. A copy would be dead code the sync
keeps restoring, which is the case REG-5's list is for. Each becomes an adopted
file the day a caller arrives.

## REG-4 after a fourth consumer

REG-4 says a registry component may name only tokens that exist in every repo
it lands in, and a fourth consumer narrows that set. The first four files
splitcart took name no colour, spacing or weight tokens at all except
`--focus-ring` and `--ring-field`, which it declares. The seven primitives do
name colours, and REG-4 is what made the token work above a prerequisite rather
than a follow-up: `--link`, `--link-hover` and `--shadow-s` were declared before
the copies landed, not after. The files it still does not take are mostly not
taken _because_ of REG-4 — the marketing band names `gap-m`, `py-l`, `mb-l`,
`gap-split` and `font-strong`, and splitcart declares one `--spacing-*` rung and
no weight ramp.

That is the rule working rather than a gap: `components/FaqSection.tsx` in this
repo used to read `var(--text-light-primary)` and four siblings declared
nowhere, which is what adopting a component onto an absent vocabulary produces.

## REG-7, and two defects it does not cover

`lib/controlState.ts` is in place and its three treatments are retrofitted
across the `components/common/*` primitives, so splitcart is on the outline
system rather than merely absent from it. One `outline-hidden` survives, at
`components/common/select.tsx:114`, and it is not the bug REG-7 bans: that is a
menu item which says "focused" with a background rather than an outline, so
there is no outline for it to cancel. It is the registry's line now rather than
splitcart's, held byte-identical in three repos.

Two accessibility defects the tokens sweep found and fixed on their own merits
are recorded in [`tokens.md`](tokens.md): `input.tsx` and `navigation-menu.tsx`
each removed the browser's focus ring and put nothing back. `input.tsx` is the
registry's file now and carries `focusFieldClassName`, so that half of the fix
is maintained upstream; `navigation-menu.tsx` is still local.
