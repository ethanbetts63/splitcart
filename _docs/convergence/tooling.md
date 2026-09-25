# Convergence plan — frontend tooling and baseline

**Type:** status and work plan. Non-normative. The binding rules are
[`frontend-baseline.md`](../../../freetheplatform/_docs/frontend-baseline.md)
(BASE-1..5) and [`lint-rules.md`](../../../freetheplatform/_docs/lint-rules.md)
LINT-2/4/9/10.

Evidence: `scratchpad/gap-tooling.md` (survey of 2026-09-25).

## Where this stands

TL-1 through TL-10 landed on 2026-09-25, and `lint:css` joined
`npm run check` when the token conversion turned it green. splitcart is the fourth consumer in
`baseline-drift.mjs`, all twenty pinned packages agree across the four repos,
and `npm run check` runs `format:check`, `lint`, `typecheck` and
`check:baseline` green.

| Check            | Result                                    |
| ---------------- | ----------------------------------------- |
| `format:check`   | clean                                     |
| `lint`           | 0 errors, 0 warnings                      |
| `typecheck`      | clean, under the levelled `tsconfig.json` |
| `check:baseline` | 20 pinned packages agree across 4 repos   |
| `build`          | compiles and prerenders 23 routes         |
| `lint:css`       | clean, and inside `npm run check`         |

## What landed, and the two decisions inside it

**The design-system ESLint block is not on yet.** allbikes and freethedesk
both run `no-restricted-syntax: designSystemNoRestrictedSyntax()` from
`freetheplatform/frontend/lint/design-system-eslint.mjs`. splitcart's
`eslint.config.mjs` imports the CSS-module boundary from the same file but
leaves that block out, with the reason written beside it. It is the ESLint
half of the same token problem `lint:css` reports, it costs several hundred
findings today, and it belongs to [`tokens.md`](tokens.md) alongside the CSS
half. It is the second thing that plan switches on.

**`@next/next/no-img-element` is off, one rule, with the reason recorded.**
`next.config.ts` sets `images.disableStaticImages: true`, every photographic
asset ships as a pre-built webp ladder (`-320w` … `-1280w`), and
`src/lib/assets.ts` turns that ladder into `src`/`srcSet`/`sizes` at the call
site. That is `next/image`'s job, done at author time. The rule's advice here
is to add a second implementation of something that already works. If the
ladder ever goes, so should the exception.

## A note for whoever does tokens.md

Turning on the design-system block and `lint:css` together is right — they are
two halves of one vocabulary — but expect the ESLint half to be much the
larger number, because splitcart's presentation lives in Tailwind class
strings rather than in CSS.

## Deliberately not here

- The `check:*` structural scripts for SEO, forms and tokens are specified in
  their own plans. This plan owns only the `check` composition they append to.
- `@freetheplatform/web-security` was a PINNED package splitcart lacked. It
  arrived with [`security.md`](security.md)'s header work on 2026-09-25, and
  the scoped row in `baseline-drift.mjs` did exactly what it was built to do:
  declaring the package failed the check in all four repos until the row was
  widened to name splitcart too. It is a plain four-repo row now.
- `zod` is the same shape, and arrives with [`forms.md`](forms.md). `marked`
  has no consumer here and should stay absent.
