# Convergence plan — SEO

**Type:** status and work plan. Non-normative. The binding rules are
[`seo-standard.md`](../../../freetheplatform/_docs/seo-standard.md) (SEO-1..9).
Read its §0 sourcing rule before touching any schema row here.

Evidence: `scratchpad/gap-seo.md` (survey of 2026-09-25).

## Resolved first: there are two sitemaps and one is dead

The survey flagged that splitcart appeared to be mid-migration, with Django
still serving a Vite SPA catch-all alongside the Next.js frontend. That is now
settled, and it changes the shape of this plan.

`config/urls.py` ends in `re_path(r'^.*', ReactAppView.as_view())`.
`ReactAppView` renders `index.html`. There is no `index.html` anywhere in the
repo, and `TEMPLATES.DIRS` / `STATICFILES_DIRS` both point at
`frontend/dist` — a Vite output directory that no longer exists.

So the catch-all does not serve a legacy SPA. It matches every unrouted path and
raises `TemplateDoesNotExist`, which means **Django answers 500 where it should
answer 404**. Django is API-only in practice. The catch-all, the two `dist`
paths and `ReactAppView` are all dead, and their removal is
[`dead-code.md`](dead-code.md) DC-1.

The Django sitemap at `config/sitemaps.py` is dead by the same reasoning — the
live sitemap is `app/sitemap.ts`. Proof they had already drifted: `/bargains`
is in the Next sitemap and absent from Django's.

## Work

| #    | Work                                                                                                                                                                                                                                                | Acceptance                                                                       |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| SEO-A | Fix the broken OG image. `lib/seo.ts`'s `defaultOgImage` is `/static/square-image.jpg`; `frontend/public/` contains only favicons. `createMetadata()` puts it on **every page**, so every social share of every splitcart URL currently links a 404. Ship a real image at a real path. | The path named by metadata exists in `public/`.                                  |
| SEO-B | Build `lib/pages.ts` with a typed `STATIC_PAGES` registry — required `updated`, `title`, `description` per route — modelled on freethedesk's. `lib/seo.ts` is only a `createMetadata()` helper today; there is no registry, which is the root cause of most rows below. Add `STATIC_NOINDEX_PAGES`, `REDIRECT_STUBS` and `DYNAMIC_ROUTE_FAMILIES` with the spellings SEO-9 requires. | Every hand-authored indexable route is exactly one typed record.                  |
| SEO-C | Introduce a single `SITE_URL` leaf module. The site origin is currently spelled four independent times — `siteUrl` in `lib/seo.ts`, `baseUrl` in `sitemap.ts`, the hardcoded sitemap URL in `robots.ts`, and `metadataBase` in `layout.tsx`.        | One module owns the origin; the other three import it.                           |
| SEO-D | Rewrite `app/sitemap.ts` to derive from the registry. It currently hardcodes 14 entries all carrying the identical literal `lastModified: "2026-06-29"` — permanently stale, never derived (SEO-3) — and emits `changeFrequency` and `priority`, which the standard says to emit neither of. | `lastModified` is the registry's `updated`; no `changeFrequency`/`priority`.      |
| SEO-E | Fix the sitemap/canonical disagreement: category URLs carry a trailing slash in the sitemap while the pages' own canonical tags do not. Pick one spelling and make both sides use it.                                                               | Sitemap URL and canonical are byte-identical for every route.                    |
| SEO-F | Stop typing the 11 category slugs by hand in three places (`data/categories.ts`, `app/sitemap.ts`, `config/sitemaps.py`). One source; the Django copy disappears with DC-1.                                                                          | One declaration of the category slug set.                                        |
| SEO-G | Add `/privacy` to the sitemap — it is indexable and in no sitemap today. Audit every other route for the same omission.                                                                                                                             | Every indexable route appears exactly once.                                      |
| SEO-H | Declare one indexation state per public route and **assert** the noindex ones in the page, not merely record them (SEO-2). `/login`, `/signup` and `/final-cart` are the candidates.                                                                | Each noindex route emits the directive from its own page.                        |
| SEO-I | Rewrite `app/robots.ts`. Several rules are trailing-slash-only (`/admin/`, `/api/`, `/final-cart/`, `/substitutions/`), which under RFC 9309 prefix matching does not cover the bare path. Use typed groups of bare prefixes with no `$` anchoring (SEO-8). Decide the AI-crawler group deliberately. `llms.txt` exists but robots.txt never points at it. | Bare prefixes; state 4 resolves from the `*` group alone.                        |
| SEO-J | Collapse four uncoordinated JSON-LD emission paths into one shared `StructuredDataScript` (SEO-7): `lib/schema.tsx`'s `JsonLdScript`, raw inline scripts on `/` and `/contact`, `FaqSection`'s own inline script, and `JsonLdItemList.tsx`. **None of them escapes `<` as `<`** — they use plain `JSON.stringify`, which is the injection hole the standard calls out. | All JSON-LD goes through one escaped emitter.                                    |
| SEO-K | Delete `JsonLdItemList.tsx`'s emission mechanism regardless of the above: it is a client component that DOM-injects into `document.head` from `useEffect`, so it is invisible in the initial HTML a crawler reads. Confirm which routes mount it, then re-emit server-side. | Structured data is present in the server-rendered HTML.                          |
| SEO-L | Build the `@id` graph (SEO-6). No node anywhere carries an `@id`, SplitCart itself never appears as a schema entity, and `JsonLdItemList`'s `Offer.seller` mints a fresh `Organization` per product instead of referencing one canonical Coles / Woolworths / Aldi node. | One business entity at a stable `@id`; every other node references it.           |
| SEO-M | Verify every schema property against schema.org and Google's docs before it ships (SEO-5). Two known suspects: `WebSite.founder` on the homepage (`founder` is an `Organization` property, not `WebSite`'s), and product `Offer`s carrying price but no `availability`, `seller` `@id`, `shippingDetails` or return policy. | Every emitted property is verified; output validated.                            |
| SEO-N | Deal with the dated price claims in `data/pillar-faqs.ts`. FAQPage content asserts specific figures ("$3.45/kg as of 2026") that surface verbatim in Google's FAQ rich results with no freshness mechanism. Either derive them or stop publishing them as facts. Only true facts get published (SEO-5). | No stale numeric claim is published as structured data.                          |
| SEO-O | Add the check scripts, adapted from `freethedesk/frontend/scripts/seo/*.mjs`: `check:og-images` first (it catches SEO-A with no registry needed), then `ts-loader.mjs`, then `check:sitemap` and `check:seo-ledger` once `lib/pages.ts` exists. Append them to `npm run check`. | All four scripts exist and exit 0.                                               |

## Ordering

SEO-A is a live user-visible defect and needs nothing else to land. SEO-B is the
keystone — SEO-D, SEO-G, SEO-H and half of SEO-O are blocked on it. SEO-J and
SEO-L are one coherent piece of work and should land together; doing SEO-L first
means building an `@id` graph inside four emitters you are about to delete.
