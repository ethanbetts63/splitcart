# SplitCart frontend

The public SplitCart site: product search and browsing, the cart, substitution
approval, and the optimised shopping plan. It is a **Next.js 16 App Router**
application deployed to Vercel at https://www.splitcart.com.au/, talking to the
Django API at `api.splitcart.com.au`.

Agents should read [`AGENTS.md`](AGENTS.md) alongside this file.

## Stack

| Piece        | What                                                                          |
| ------------ | ----------------------------------------------------------------------------- |
| Framework    | Next.js 16, App Router, React 19                                              |
| Language     | TypeScript                                                                    |
| Styling      | Tailwind CSS v4 via `@tailwindcss/postcss`, one stylesheet at `src/index.css` |
| Components   | Radix primitives under `src/components/ui/`, originally from `shadcn`         |
| Server state | TanStack Query, provided in `src/app/providers.tsx`                           |
| Client state | React context: `AuthContext`, `CartContext`, `DialogContext`                  |
| Analytics    | `@vercel/analytics`                                                           |

## Run it

```powershell
npm install
npm run dev
```

The app runs at `http://localhost:3000`. `next.config.ts` rewrites `/api/:path*`
to `DJANGO_API_URL`, which defaults to `http://localhost:8000` — so a local
Django server is picked up with no configuration. To point at the deployed API
instead, set `DJANGO_API_URL` and `NEXT_PUBLIC_DJANGO_API_URL` in
`.env.local`.

| Script              | Does                                       |
| ------------------- | ------------------------------------------ |
| `npm run dev`       | Development server                         |
| `npm run build`     | Production build                           |
| `npm run start`     | Serve a production build                   |
| `npm run check`     | Static checks — run this before committing |
| `npm run format`    | Prettier, writing                          |
| `npm run lint`      | ESLint over `src`                          |
| `npm run typecheck` | `tsc --noEmit`                             |

`check` is the umbrella: formatting, lint, typecheck and the structural
checks. The individual scripts are there for iterating.

## Structure

```
src/
├── app/               # Routes. layout, providers, shell, sitemap.ts, robots.ts,
│                      # and one folder per route
├── page_components/   # The body of each page; page.tsx files stay thin
├── components/        # Shared components
│   └── ui/            # Primitives (button, dialog, select, ...)
├── context/           # AuthContext, CartContext, DialogContext
├── services/          # apiClient.ts and one *.api.ts per endpoint family
├── hooks/             # useApiQuery, useMediaQuery, use-mobile
├── lib/               # apiUrl, seo, schema, companies, assets, utils
├── data/              # Static content: category icons and copy, pillar FAQs
├── types/             # One type per file, re-exported from index.ts
├── assets/            # SVG and image assets
└── index.css          # The only stylesheet
```

## How it talks to the API

`services/apiClient.ts` is the only place that calls `fetch` against Django.
`ApiClient` attaches `Authorization: Token <token>` when the user is signed in
and `X-Anonymous-ID` when they are not, so an anonymous visitor keeps a cart
across page loads and that cart is merged into their account on login.

Endpoint families get a `*.api.ts` module (`cart.api.ts`, `product.api.ts`)
that takes an `ApiClient`. Components call those through a context or a
TanStack Query hook — never `fetch` directly.

## The cart, and why it debounces

Cart edits are optimistic: `addItem` and `updateItemQuantity` update local
state immediately and schedule a debounced `POST /api/carts/sync/` that sends
the whole cart after a pause in activity. One request per burst of clicking
rather than one per click.

Sync returns the substitutions the backend found for the cart's items. The user
approves or rejects those, then `POST /api/carts/{id}/optimize/` returns the
plans — a best single company and a split across two, three or four — which
`FinalCartPage` renders, with PDF and email export.

The optimisation itself is backend work; see
[`../_docs/optimization.md`](../_docs/optimization.md) for the algorithm and
[`../_docs/substitutions.md`](../_docs/substitutions.md) for how substitutes
are matched.

## Ordering and bargains

Product lists support several orderings, all resolved server-side:

- **Bargain-first** — the default on category pages. `ProductPriceSummary`
  supplies pre-computed candidates cheaply, then the backend recomputes the
  real discount for that shortlist against current prices and sorts by it.
  Products with no live discount fall back to unit price.
- **Relevance** — the default for text search. Scored on how well name, brand
  and size match the query. Bargain scoring is not applied to search results.
- **Price** ascending or descending, and **unit price** ascending.

The summary table behind bargain-first is rebuilt by
`python manage.py generate --price-summaries` on the server. See
[`../_docs/product_price_summary.md`](../_docs/product_price_summary.md) and
[`../_docs/bargains.md`](../_docs/bargains.md).
