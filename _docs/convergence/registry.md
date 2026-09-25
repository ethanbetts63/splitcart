# Convergence plan — component registry

**Type:** status and work plan. Non-normative. The binding rules are
[`component-registry.md`](../../../freetheplatform/_docs/component-registry.md)
(REG-1..7).

## Status: a narrow consumer

splitcart joined `CONSUMERS` in
`freetheplatform/frontend/registry/scripts/sync.mjs` on 2026-09-25 and takes
four files, each carrying the `/* Component registry: … */` banner and held
byte-identical by `sync.mjs --check`:

| File                                      | What it brought                                            |
| ----------------------------------------- | ---------------------------------------------------------- |
| `lib/utils.ts`                            | `cn()` taught the nine type rungs, maintained in one place |
| `lib/controlState.ts`                     | The three focus treatments and the two disabled reasons    |
| `types/FaqItem.ts`                        | The FAQ item, with its optional in-answer links            |
| `components/seo/StructuredDataScript.tsx` | The JSON-LD emitter that escapes `<`                       |

Everything else in the registry has a `SCOPED` row in `sync.mjs` giving the
reason it would be dead code here today (REG-5). Those reasons are the record
of how splitcart differs; read them there rather than restating them.

Two things this made true that are worth knowing:

- `lib/utils.ts` had to be split first. The registry's version is `cn()` and
  nothing else. `getCsrfToken`/`getAuthHeaders` are now `lib/authHeaders.ts`
  and `debounce` is `lib/debounce.ts`.
- `lib/schema.tsx` is a one-line forward to the registry path, because the
  five route files that import `@/lib/schema` are outside this plan's reach.
  There is still exactly one emitter.

## Work still open

| #     | Work                                                                                                                                                                                                                                                                                                                                                                                        | Blocked on                                                  |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| RG-7  | Adopt the eleven shadcn primitives. **This is a reconciliation, not a byte-copy** — all ten that exist locally have diverged from the registry's, 170 changed lines in total (measured 2026-09-25): `button` 56, `select` 26, `input` 19, `badge` 18, `checkbox` 14, `table` 9, and `alert`, `card`, `label`, `spinner` 7 each. Every hunk needs a verdict: the registry's version wins, or splitcart's is the improvement and goes upstream instead. Needs the directory move below, plus three tokens the registry's copies name and splitcart does not declare: `--color-link` and `--color-link-hover` (`button.tsx`'s `link` variant) and `--shadow-s` (`select.tsx`'s popover); all three confirmed absent from `tokens.css`. `textarea.tsx` is the eleventh and would arrive with no importer, so it needs one or its own `SCOPED` row. | the move; three tokens in `src/styles/tokens.css`           |
| RG-9  | Move the shadcn family from `src/components/ui/` to `src/components/common/`, the registry's path for it. **25 files import from `ui/`, not the nine this row used to claim** — counted 2026-09-25 — and most are in `src/components/`, not the `src/app/` and `src/page_components/` the old text sent you to. `components/ui/` also holds five files that are splitcart's own and not registry primitives (`login-form.tsx`, `signup-form.tsx`, the two `*.schema.ts` beside them, and `settings-dialog.tsx`); they are not part of the shadcn family and do not follow it into `common/`. Until then `sync.mjs` scopes all eleven primitives away from splitcart.                                                                                                                | —                                                           |
| RG-10 | Delete `src/lib/schema.tsx` and repoint `app/page.tsx`, `app/bargains/page.tsx`, `app/categories/[slug]/page.tsx`, `app/contact/page.tsx` and `app/privacy/page.tsx` at `@/components/seo/StructuredDataScript`.                                                                                                                                                                            | —                                                           |
| RG-11 | Adopt `marketing/FaqSection.tsx`, `marketing/renderFaqAnswer.tsx` and `common/eyebrow.tsx`, replacing the local `components/FaqSection.tsx`.                                                                                                                                                                                                                                                | [`tokens.md`](tokens.md) TK-15, plus a `font-weight-*` ramp |

### Why RG-9 is a directory move and not a `sync.mjs` option

The obvious fix is a per-repo destination override in `sync.mjs` — land
`components/common/*` at `components/ui/*` for splitcart alone. It was
considered and rejected.

`sync.mjs` is a literal file copy with no path rewriting, and that is
load-bearing rather than incidental: registry files import each other by
absolute alias, `@/components/common/eyebrow` and
`@/components/seo/StructuredDataScript` among them. An override would have to
rewrite import specifiers as well as destinations, which turns a byte copy into
a transform and takes REG-1's drift check from a plain `diff` to a comparison
that has to know what the transform was. That is a permanent cost on tooling
three other repositories depend on, paid to avoid a one-off rename in the repo
that is out of step. The rename is the cheaper side.

## REG-4 after a fourth consumer

REG-4 says a registry component may name only tokens that exist in every repo
it lands in, and a fourth consumer narrows that set. The four files splitcart
takes name no colour, spacing or weight tokens at all except `--focus-ring` and
`--ring-field`, which it declares, so nothing already in the registry had to
change. The files it does not take are mostly not taken _because_ of REG-4 —
the marketing band names `gap-m`, `py-l`, `mb-l`, `gap-split` and `font-strong`,
and splitcart declares one `--spacing-*` rung and no weight ramp.

That is the rule working rather than a gap: `components/FaqSection.tsx` in this
repo used to read `var(--text-light-primary)` and four siblings declared
nowhere, which is what adopting a component onto an absent vocabulary produces.

## REG-7, and two defects it does not cover

`lib/controlState.ts` is in place and its three treatments are retrofitted
across fifteen `components/ui/*` primitives, so splitcart is on the outline
system rather than merely absent from it. One `outline-hidden` survives, at
`components/ui/select.tsx:103`, and it is not the bug REG-7 bans: that is a
menu item which says "focused" with a background rather than an outline, so
there is no outline for it to cancel.

Two accessibility defects the tokens sweep found and fixed on their own merits
are recorded in [`tokens.md`](tokens.md): `input.tsx` and
`navigation-menu.tsx` each removed the browser's focus ring and put nothing
back.
