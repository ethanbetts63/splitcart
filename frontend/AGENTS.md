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
| `src/components/forms/`  | Login, signup and the two password-reset forms, each beside its Zod schema and Server Action                        |
| `src/context/`           | `AuthContext`, `CartContext`, `DialogContext` — composed in `app/providers.tsx`                                     |
| `src/services/`          | `apiClient.ts` plus one `*.api.ts` module per endpoint family                                                       |
| `src/hooks/`             | `useApiQuery`, `useMediaQuery`, `use-mobile`                                                                        |
| `src/lib/`               | `serverApi`, `catalogue`, `apiUrl`, `seo`, `companies`, `assets`, `utils`, `controlState`                           |
| `src/types/`             | One exported type per file, re-exported from `index.ts`                                                             |
| `src/data/`              | Static content: category icons and copy, pillar-page FAQs                                                           |
| `src/index.css`          | The only stylesheet. Tailwind import, `@theme inline`, and the token block                                          |

## The API boundary

- `lib/serverApi.ts` owns `DJANGO_API_URL` and is the only file that reads it
  (FORMS-9). Everything server-side goes through it: the four ISR pages via
  `lib/catalogue.ts`, the Server Actions via `serverApiFetch`, and `proxy.ts`.
- The browser calls only `/api/*` on its own origin. `src/proxy.ts` rewrites
  that to Django and attaches the visitor's address beside `FTP_PROXY_SECRET`,
  so Django's per-IP throttles key on the visitor rather than on Vercel. There
  is no `NEXT_PUBLIC_` API variable and no CORS.
- Sessions are `freetheplatform.auth`'s HttpOnly cookies, `splitcart_access`
  and `splitcart_refresh`; no script can read them. `services/apiClient.ts`
  exports the shared `authedFetch` (deadline, CSRF, one refresh in flight) and
  is the only place browser code calls Django; a signed-out shopper is still
  identified by `X-Anonymous-ID`. Add an endpoint as a `*.api.ts` module that
  uses `ApiClient`; do not call `fetch` from a component.
- Login, signup and password reset are Server Actions: they call Django once
  and relay its `Set-Cookie` with the registry's `lib/serverCookies.ts`.
- A catalogue read that fails throws (`lib/catalogue.ts`). A production build
  needs Django reachable at `DJANGO_API_URL` and fails, naming the URL, when it
  is not; it used to prerender empty pages instead.

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
