"""Which product pages search engines may index.

A product page earns a place in search when it answers the question people
search for: what this costs at one chain against another. So a product
qualifies when at least two of Aldi, Coles and Woolworths carry a price for it,
each scraped within `INDEXABLE_PRICE_MAX_AGE_DAYS`. Coles and Woolworths
together qualify; Aldi qualifies only beside one of them, which is rare (Aldi is
mostly its own brands) and is the most useful page when it happens. IGA does not
count: its prices are store-level and never a chain-wide comparison.

Everything else stays reachable and `noindex`: a single-chain page repeats the
chain's own price, which the chain's own page will always outrank, and a stale
price is worse than no page. The rule runs on every request, so the set follows
the scrapes without anyone curating it: a product joins the sitemap when it
qualifies and drops back to `noindex` when it stops.

There are two spellings of the one rule — a queryset for the sitemap and a test
over prefetched prices for a single page — and `test_indexable.py` holds them
to the same answers.
"""

from datetime import date, timedelta

from django.conf import settings
from django.db.models import Count
from django.utils import timezone

from products.models import Price, Product

COMPARED_CHAINS = ('Aldi', 'Coles', 'Woolworths')
MIN_CHAINS = 2


def fresh_since(today: date | None = None) -> date:
    """The oldest scrape date that still counts as current."""
    return (today or timezone.localdate()) - timedelta(days=settings.INDEXABLE_PRICE_MAX_AGE_DAYS)


def indexable_products(today: date | None = None):
    """Every product whose page is indexable, as a queryset."""
    qualifying = (
        Price.objects.filter(company__name__in=COMPARED_CHAINS, scraped_date__gte=fresh_since(today))
        .order_by()
        .values('product_id')
        .annotate(chains=Count('company', distinct=True))
        .filter(chains__gte=MIN_CHAINS)
        .values('product_id')
    )
    return Product.objects.filter(id__in=qualifying)


def is_indexable(prices, today: date | None = None) -> bool:
    """The same rule over one product's prices, already loaded with their company."""
    since = fresh_since(today)
    chains = {
        price.company.name
        for price in prices
        if price.company.name in COMPARED_CHAINS and price.scraped_date >= since
    }
    return len(chains) >= MIN_CHAINS
