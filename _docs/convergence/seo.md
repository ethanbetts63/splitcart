# Convergence plan — SEO

**Type:** status and work plan. Non-normative. The binding rules are
[`seo-standard.md`](../../../freetheplatform/_docs/seo-standard.md) (SEO-1..9).
Read its §0 sourcing rule before touching any schema row here.

Evidence: `scratchpad/gap-seo.md` (survey of 2026-09-25).

SEO-A through SEO-N landed on 2026-09-25. What is left is one wiring step.

## Work

| #     | Work                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Acceptance                                |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| SEO-O | Append the three SEO checks to `npm run check`: `"check:og-images": "node scripts/check-og-images.mjs"`, `"check:sitemap": "node scripts/check-sitemap-routes.mjs"`, `"check:seo-ledger": "node scripts/check-indexation-ledger.mjs"`. The scripts and their engines exist under `frontend/scripts/` and each exits 0 when run directly; only the `package.json` entries are missing, because that file belonged to another session when the rest landed. | The three names run from `npm run check`. |

## Decisions taken while the rest landed

Recorded because each one is a judgement a later reader would otherwise
re-litigate, and two of them changed live crawler behaviour.

**`/product` and `/search` are disallowed, not noindexed.** Both carried both
states, which seo-standard.md §2 forbids: a disallowed page is never fetched, so
the `noindex` on it is never read. Both are unbounded generated surfaces backed
by a live Django fetch, so the disallow is the real statement and the `noindex`
metadata was the inert half. It is gone from those two pages. If `/product` is
ever opened to crawlers, that page needs a fresh indexation decision — there is
no longer a leftover one to inherit.

**`/login`, `/signup`, `/final-cart` and `/substitutions` went the other way.**
They are four bounded application pages, so they are noindex-only now and are no
longer in the robots disallow. Googlebot will start fetching them, read the
directive, and keep them out of the index — which is what the disallow could
never achieve on its own.

**The AI-crawler group excludes `/product`.** The shared standard says answer
engines get the whole public site minus capability URLs and `/api`. SplitCart
adds `/search` and `/product`, and the reason for `/product` is not crawl budget
but origin load: tens of thousands of pages, each a live fetch against one small
Django instance. The reasoning is written into `app/robots.txt/route.ts` so it
can be reversed deliberately.

**`absoluteUrl` emits no trailing slash, the homepage included.** Next
normalises `alternates.canonical` and `openGraph.url` against `trailingSlash` in
`next.config.ts` and strips one whatever is passed, so `{SITE_URL}/` in the
sitemap would have disagreed with `{SITE_URL}` in the `<head>` — the exact
mismatch the helper exists to prevent. If `trailingSlash` is ever turned on,
`absoluteUrl` is the one place to change.

**Offers carry price and seller and nothing else.** No `availability` (no live
stock state reaches the frontend — the scrape carries prices, not stock), no
`shippingDetails` and no `hasMerchantReturnPolicy` (they would be Coles' and
Woolworths' terms, which SplitCart neither sets nor honours). These stay absent
until they are true. This is a product-snippet aggregation, not a merchant
listing.

**`WebSite.potentialAction` is gone.** Google removed the sitelinks searchbox
from Search in October 2024 and archived the documentation, so the `SearchAction`
claimed an outcome that no longer exists.

## Owed, not blocked

- `frontend/src/types/JsonLdItemListProps.ts` and its re-export from
  `types/index.ts` are dead now that `JsonLdItemList` is gone. They belonged to
  another session's scope when the component was removed.
- `next.config.ts` still redirects `/pillar-pages/*` to trailing-slash category
  URLs (`/categories/dairy-and-eggs/`), which 308 again to the canonical
  slashless form. One extra hop on four legacy URLs; worth collapsing when that
  file is next opened.
- The FAQ copy in `page_components/HomePage.tsx`, `BargainsPage.tsx` and
  `SubstitutionPage.tsx` is also emitted as `FAQPage` structured data and was
  not audited for the dated-price problem SEO-N fixed in `data/pillar-faqs.ts`.
- `StructuredDataScript` lives in `lib/schema.tsx` rather than
  `components/seo/`. It moves when splitcart becomes a component-registry
  consumer ([`registry.md`](registry.md)); the four engine files under
  `frontend/scripts/seo/` are local copies for the same reason, each marked with
  its provenance.
