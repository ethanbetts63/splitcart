# Convergence plan — dead code

**Type:** status and work plan. Non-normative.

The Vite-to-Next migration completed in the source and never completed in
everything around it. What follows is residue: code and configuration that is
reachable by no caller, renders no template, and serves no route.

Evidence: `scratchpad/gap-tooling.md`, `gap-tokens.md`, `gap-seo.md`,
`gap-docs.md`, `gap-forms.md` (surveys of 2026-09-25), plus direct verification.

## The one that is not merely inert

`config/urls.py` ends with:

```python
re_path(r'^.*', ReactAppView.as_view(), name='react_app')
```

`ReactAppView` is a `TemplateView` rendering `index.html`. There is no
`index.html` anywhere in the repository. `TEMPLATES.DIRS` and `STATICFILES_DIRS`
both point at `frontend/dist`, the Vite output directory, which no longer
exists.

The pattern `^.*` matches **every** path Django does not route earlier. So every
unmatched request — every typo'd URL, every crawler probing a path, every
request that should be a clean 404 — reaches a view that raises
`TemplateDoesNotExist` and returns a 500.

This is not dormant dead code. It is dead code that changes the response of a
live production API, and it is the reason DC-1 goes first.

## Work

| #    | Remove                                                                                                                                                                       | Why it is dead                                                                                               |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| DC-1 | The `re_path(r'^.*', ReactAppView...)` catch-all, `pipeline/views/react_app_view.py`, the `frontend/dist` entry in `TEMPLATES.DIRS`, and `STATICFILES_DIRS`.                  | No template, no `dist/`. Django is API-only in practice. Turns 500s back into 404s.                          |
| DC-2 | `config/sitemaps.py` and its `sitemap.xml` route.                                                                                                                            | The live sitemap is `app/sitemap.ts`. The two had already drifted — `/bargains` is in one and not the other. |
| DC-3 | The `pillar_page_redirect` view and `_PILLAR_SLUG_MAP`, **only if** the old `/pillar-pages/<slug>/` URLs are confirmed unreferenced by live traffic. Otherwise keep and move the redirect to the frontend. | Needs a look at real traffic before deleting; a 301 that still has referrers is not dead code. Do not guess. |
| DC-4 | `src/App.css`.                                                                                                                                                               | Unmodified Vite template CSS — the React logo spin animation. Zero importers.                                |
| DC-5 | `src/assets/splitcart_symbol_v6 - Copy.png` and `splitcart_symbol_v6_navy.png`.                                                                                               | Unreferenced.                                                                                                |
| DC-6 | `components.json`.                                                                                                                                                           | shadcn generator config. The family removed it repo-wide; Radix stays as ordinary dependencies.              |
| DC-7 | The two dead cart-export call sites in `FinalCartPage.tsx` — `POST /api/cart/email-list/` and `/api/cart/download-list/`.                                                     | Neither path is routed anywhere in Django. They 404 in production today. Shared with [`forms.md`](forms.md) FM-2. |
| DC-8 | The Vite-era origins in `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` — `http://localhost:5173`.                                                                          | The Vite dev server is gone. (The rest of the CORS block is [`security.md`](security.md)'s, not this plan's.) |
| DC-9 | `node_modules/.package-lock.json` from git tracking.                                                                                                                         | Tracked despite `node_modules/` being ignored — the single tracked artefact in the repo.                    |
| DC-10 | `_docs/deprecated_gs1.md`, `_docs/deprecated_iga_and_store_selection.md`, `_docs/deprecated_store.md`.                                                                       | Unreferenced. `deprecated_store.md` documents a `Store` model that no longer exists in code.                 |

## DC-3 is the one to be careful with

Every other row is safe on the evidence already gathered. DC-3 is a permanent
redirect serving URLs that were once public, and "no code references it" is not
the same as "no visitor uses it". Check Search Console or server logs for
`/pillar-pages/` traffic before removing it, and if in doubt keep the redirect
and move it to the Next.js side — a 301 costs almost nothing and a broken old
URL costs a ranked page.
