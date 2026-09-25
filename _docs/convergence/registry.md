# Convergence plan — component registry

**Type:** status and work plan. Non-normative. The binding rules are
[`component-registry.md`](../../../freetheplatform/_docs/component-registry.md)
(REG-1..7).

Evidence: `scratchpad/gap-registry.md` (survey of 2026-09-25).

## Status: not a consumer

splitcart has no `CONSUMERS` entry in `sync.mjs` and no
`/* Component registry: ... */` banner anywhere in `src/`. It takes no registry
copies today, so REG-1 and REG-2 are vacuously satisfied and mean nothing.
Becoming a consumer is the work.

## shadcn and the registry coexist — this matters

The survey settled a question that decides the whole shape of this plan.
`sync.mjs`'s `SHADCN = ['allbikes', 'bloomprint']` list *is* the shadcn
primitives, synced into those repos at `components/common/`. freethedesk
deliberately has none and runs its own non-shadcn `ui/` family;
`component-convergence.md` names that gap explicitly.

So splitcart's stock shadcn install is not something to rip out. It is
reconciled file by file:

- **12 primitives overlap** the registry's shadcn set — these become registry
  copies once tokens land.
- **17 extra shadcn files** have no registry counterpart and stay local.
- **One path mismatch**: splitcart keeps shadcn at `components/ui/`, the
  registry assumes `components/common/`. `sync.mjs` has no per-repo path
  override today. Either add one, or move splitcart's directory. That decision
  belongs in freetheplatform and blocks the primitive adoption row.

## What splitcart should take, and when

| Registry file                                              | splitcart today                                              | Verdict                                                                 |
| ---------------------------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------- |
| `seo/StructuredDataScript.tsx`                             | `lib/schema.tsx` `JsonLdScript` + `JsonLdItemList.tsx`       | **Adopt — zero prerequisites.** Both local copies skip `</script>` escaping; the registry closes a real injection hole. Lands with [`seo.md`](seo.md) SEO-J. |
| `types/FaqItem.ts`                                         | `types/FaqSectionProps.ts`                                   | **Adopt — zero prerequisites.** Shape already matches.                  |
| `marketing/FaqSection.tsx`                                 | `components/FaqSection.tsx`                                  | Adopt after tokens. Same job, near-identical `{question, answer}` props. |
| 11 shadcn primitives                                       | 12 of `components/ui/*`                                      | Adopt after tokens **and** the path decision.                           |
| `lib/utils.ts` (cn + text-scale)                           | `lib/utils.ts` (cn + CSRF/auth/debounce, mixed together)     | Blocked — splitcart's file must be split first.                         |
| `layout/SiteHeader.tsx`, `SiteFooter.tsx`, `Breadcrumbs.tsx`, nav family | `NavBar.tsx`, `Footer.tsx`, ad-hoc breadcrumbs  | **Stays local.** Genuinely different shells, not skins. Out of scope for a first copy. |
| `SignaturePad`, `ClarityAnalytics`, `GoogleAnalytics`, `articles.ts`, `author.ts`, `serverCookies.ts`, `status-chip.tsx` | none | Not needed — no signing flow, no analytics plumbing, no blog, and no cookie relay to serve. |

## REG-4 is the gate

A registry component may name only tokens that exist in every repo. splitcart's
`index.css` is stock shadcn and declares **zero** of the registry's required
surface / border / text / action / type-scale / spacing / layout tokens.

`FaqSection.tsx` already demonstrates the failure mode: it reads
`var(--text-light-primary)` and four siblings that are declared nowhere and
resolve to nothing. That is a live rendering bug today, and it is exactly what
adopting a registry component onto an absent token vocabulary produces at scale.

[`tokens.md`](tokens.md) TK-2 through TK-7 is therefore a hard prerequisite for
every row above except the first two.

## Sequence

| #    | Work                                                                                                                                                                | Blocked on                       |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| RG-1 | Add splitcart to `CONSUMERS` in `freetheplatform/frontend/registry/sync.mjs` (same commit as [`tooling.md`](tooling.md) TL-1's `baseline-drift.mjs` edit).           | —                                |
| RG-2 | Adopt `StructuredDataScript.tsx` and `types/FaqItem.ts` — the two zero-prerequisite copies.                                                                          | —                                |
| RG-3 | Split `lib/utils.ts`: move CSRF, auth and debounce helpers out so the file can become a registry copy.                                                              | —                                |
| RG-4 | Fix the two `className`-passthrough drift sites: `NavSearchBar.tsx:9,20` and `NextButton.tsx:8,21`. The latter is used by `FloatingNextButton.tsx:27` to fully reposition and resize the button — textbook drift wearing a prop's clothes (REG-6). Replace with closed appearance props carrying identity-level reasons. | —                                |
| RG-5 | Add `lib/controlState.ts` and retrofit the three named focus treatments (REG-7).                                                                                     | [`tokens.md`](tokens.md) TK-7    |
| RG-6 | Decide the `ui/` vs `common/` path mismatch in `sync.mjs` — per-repo override, or move splitcart's directory.                                                        | —                                |
| RG-7 | Adopt `FaqSection.tsx` and the 11 shadcn primitives.                                                                                                                 | TK-2..TK-7, RG-6                 |
| RG-8 | Write the `SCOPED` rows with real, non-aspirational reasons (REG-5): exclude `SignaturePad`, `serverCookies.ts`, `articles.ts`/`prose.css`, `author.ts`, `status-chip.tsx`, both analytics components, `breadcrumbs.ts`, `routePolicy.ts`. | RG-7                             |

## A note on REG-7

splitcart's 20 `outline-none` / `outline-hidden` occurrences are all in
unmodified `components/ui/*`, and none currently hits the outline-cancels-outline
bug REG-7 bans — only because splitcart is not on the outline system at all.
That is not compliance, it is absence. Two of them — `input.tsx:11` and
`navigation-menu.tsx:94` — remove the focus ring and put nothing back, which is
an accessibility defect independent of any registry work.
