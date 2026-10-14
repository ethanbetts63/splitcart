# Convergence plan — SEO

**Type:** status and work plan. Non-normative. The binding rules are
[`seo-standard.md`](../../../freetheplatform/_docs/seo-standard.md) (SEO-1..9).
Read its §0 sourcing rule before touching any schema row here.

Evidence: `scratchpad/gap-seo.md` (survey of 2026-09-25).

SEO-A through SEO-O landed on 2026-09-25. No rows remain; what follows is the
record of the decisions taken, kept because each is one a later reader would
otherwise re-litigate.

## Decisions taken while the rest landed

Recorded because each one is a judgement a later reader would otherwise
re-litigate, and two of them changed live crawler behaviour.

**`/search` is disallowed, not noindexed.** It carried both states, which
seo-standard.md §2 forbids: a disallowed page is never fetched, so the `noindex`
on it is never read. Every distinct `?q=` is a new URL, so the disallow is the
real statement and the `noindex` was the inert half.

**`/product` was disallowed too, and was opened on 2026-10-14.** It is now a
conditional family: a product page is indexable when at least two of Aldi, Coles
and Woolworths carry a price for it scraped within `INDEXABLE_PRICE_MAX_AGE_DAYS`
(14), and `noindex` otherwise (`products/utils/indexable.py`; the page reads
`indexable` from the detail endpoint, the sitemap lists
`/api/products/indexable/`). Two things changed the 2026-09-25 decision:

- Search Console showed fifteen indexable URLs earning about five clicks a week,
  while the competitors ranking for single-product price searches (Grocerize,
  BuyWisely) do it with a page per product.
- The objection was origin load, and it is answered by caching rather than by
  hiding: `generateStaticParams` returning `[]` plus `revalidate = 86400` makes
  each page an ISR page, so Django sees at most one fetch per product per day
  however often it is crawled.

A single-chain product stays `noindex` because its page only repeats the chain's
own price, which the chain's own page will always outrank; a stale price stays
`noindex` because an old price presented as current is worse than no page. The
title, description and on-page summary all carry the scrape date
(`lib/productPage.ts`).

**`/login`, `/signup`, `/final-cart` and `/substitutions` went the other way.**
They are four bounded application pages, so they are noindex-only now and are no
longer in the robots disallow. Googlebot will start fetching them, read the
directive, and keep them out of the index — which is what the disallow could
never achieve on its own.

**The AI-crawler group excludes `/search`.** The shared standard says answer
engines get the whole public site minus capability URLs and `/api`; SplitCart
adds `/search`, a dead end for any crawler. It excluded `/product` as well, on
origin load, until that was answered by caching on 2026-10-14.

**Pages render whole; nothing streams.** Until 2026-10-14 `app/shell.tsx`
wrapped every page in a `Suspense` boundary whose fallback was the loading
spinner. That made every page stream: the 200 went out before the page ran, so
`notFound()` answered 200 with a 404 body (a soft 404 at every unknown category
URL in production) and `permanentRedirect()` never reached the status line. The
fallback's loading message was also an `<h1>`, so every page served two. The
boundary now sits only on `/search`, which needs it for `useSearchParams`, and
the spinner's message is a paragraph.

**`absoluteUrl` emits no trailing slash, the homepage included.** Next
normalises `alternates.canonical` and `openGraph.url` against `trailingSlash` in
`next.config.ts` and strips one whatever is passed, so `{SITE_URL}/` in the
sitemap would have disagreed with `{SITE_URL}` in the `<head>` — the exact
mismatch the helper exists to prevent. If `trailingSlash` is ever turned on,
`absoluteUrl` is the one place to change.

**Offers carry price and seller and nothing else** (`buildProductSchema`). No `availability` (no live
stock state reaches the frontend — the scrape carries prices, not stock), no
`shippingDetails` and no `hasMerchantReturnPolicy` (they would be Coles' and
Woolworths' terms, which SplitCart neither sets nor honours). These stay absent
until they are true. This is a product-snippet aggregation, not a merchant
listing.

**`WebSite.potentialAction` is gone.** Google removed the sitelinks searchbox
from Search in October 2024 and archived the documentation, so the `SearchAction`
claimed an outcome that no longer exists.

## Owed, not blocked

- The FAQ copy in `page_components/HomePage.tsx`, `BargainsPage.tsx` and
  `SubstitutionPage.tsx` is also emitted as `FAQPage` structured data and was
  not audited for the dated-price problem SEO-N fixed in `data/pillar-faqs.ts`.
