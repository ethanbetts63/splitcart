# Agent instructions — frontend

Read [`../AGENTS.md`](../AGENTS.md) first. This file adds what is specific to
`frontend/`.

## What this is

A **Next.js 16 App Router** application: React 19, TypeScript, Tailwind CSS v4
(through `@tailwindcss/postcss`), Radix primitives, and TanStack Query. It is
not a Vite SPA and has not been one for some time — if a document, a comment or
your own recollection says Vite, React Router or `dist/`, it is out of date.

Next ships version-matched documentation inside the installed package at
`node_modules/next/dist/docs/`. Read the relevant guide there before writing
App Router code; it matches the installed version, which your training data
does not.

## Layout

| Path                     | Holds                                                                                                               |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `src/app/`               | Routes. `layout.tsx`, `page.tsx`, `providers.tsx`, `shell.tsx`, `sitemap.ts`, `robots.ts`, and one folder per route |
| `src/page_components/`   | The body of each page, imported by the thin `page.tsx` in the matching route                                        |
| `src/components/`        | Shared components                                                                                                   |
| `src/components/common/` | The shadcn/Radix primitives. Seven are registry copies, the rest are local                                          |
| `src/components/forms/`  | `login-form` and `signup-form`, each beside its Zod schema                                                          |
| `src/context/`           | `AuthContext`, `CartContext`, `DialogContext` — composed in `app/providers.tsx`                                     |
| `src/services/`          | `apiClient.ts` plus one `*.api.ts` module per endpoint family                                                       |
| `src/hooks/`             | `useApiQuery`, `useMediaQuery`, `use-mobile`                                                                        |
| `src/lib/`               | `apiUrl`, `seo`, `companies`, `assets`, `utils`, `controlState`                                                     |
| `src/types/`             | One exported type per file, re-exported from `index.ts`                                                             |
| `src/data/`              | Static content: category icons and copy, pillar-page FAQs                                                           |
| `src/index.css`          | The only stylesheet. Tailwind import, `@theme inline`, and the token block                                          |

## The API boundary

- `next.config.ts` rewrites `/api/:path*` to `DJANGO_API_URL`, defaulting to
  `http://localhost:8000`. `src/lib/apiUrl.ts` resolves the browser-side base
  from `NEXT_PUBLIC_DJANGO_API_URL`.
- `services/apiClient.ts` is the only place that calls `fetch` against the
  Django API. It attaches `Authorization: Token <token>` for a signed-in user
  and `X-Anonymous-ID` for an anonymous one, via `getAuthHeaders` in
  `lib/utils.ts`. Add an endpoint as a `*.api.ts` module that uses `ApiClient`;
  do not call `fetch` from a component.
- The session model is DRF `TokenAuthentication`, not the cookie-JWT scheme the
  other repositories use. Changing it is a planned migration with a live blast
  radius — read [`../_docs/convergence/auth-migration.md`](../_docs/convergence/auth-migration.md)
  before touching auth.

## Styling and tokens

The token block in `src/index.css` is still close to unmodified `shadcn init`
output; splitcart does not yet declare the shared semantic vocabulary. Before
adding a colour, a spacing value, a radius or a text size, read
[`../../freetheplatform/_docs/token-contract.md`](../../freetheplatform/_docs/token-contract.md)
and [`../_docs/convergence/tokens.md`](../_docs/convergence/tokens.md) — the
second says how far the conversion has got, so you neither invent a name that
is about to exist nor assume one already does.

## Verification

From `frontend/`:

```
npm run check     # static checks
npm run build     # production build
```

Run both for any change that touches rendering.

Metadata, structured data, sitemap entries and robots rules are governed by
[`../../freetheplatform/_docs/seo-standard.md`](../../freetheplatform/_docs/seo-standard.md);
read its sourcing rule before changing any of them, and see
[`../_docs/convergence/seo.md`](../_docs/convergence/seo.md) for what splitcart
currently does differently.
