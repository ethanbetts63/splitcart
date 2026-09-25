# Convergence plan — dead code

**Type:** status and work plan. Non-normative.

The Vite-to-Next migration completed in the source and never completed in
everything around it. What follows is residue: code and configuration that is
reachable by no caller, renders no template, and serves no route.

Evidence: `scratchpad/gap-tooling.md`, `gap-tokens.md`, `gap-seo.md`,
`gap-docs.md`, `gap-forms.md` (surveys of 2026-09-25), plus direct verification.

## Work

| #    | Remove                                                                                                                                                                                                     | Why it is dead                                                                                                    |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| DC-3 | The `pillar_page_redirect` view and `_PILLAR_SLUG_MAP`, **only if** the old `/pillar-pages/<slug>/` URLs are confirmed unreferenced by live traffic. Otherwise keep and move the redirect to the frontend. | Needs a look at real traffic before deleting; a 301 that still has referrers is not dead code. Do not guess.      |
| DC-7 | The two dead cart-export call sites in `FinalCartPage.tsx` — `POST /api/cart/email-list/` and `/api/cart/download-list/`.                                                                                  | Neither path is routed anywhere in Django. They 404 in production today. Shared with [`forms.md`](forms.md) FM-2. |

## DC-3 is the one to be careful with

DC-3 is a permanent redirect serving URLs that were once public, and "no code
references it" is not the same as "no visitor uses it". Check Search Console or
server logs for `/pillar-pages/` traffic before removing it, and if in doubt
keep the redirect and move it to the Next.js side — a 301 costs almost nothing
and a broken old URL costs a ranked page.

Its behaviour is pinned by `config/tests/test_urls.py`, so removing it means
deleting those tests in the same commit rather than leaving them as the only
surviving record of a route nothing serves.
