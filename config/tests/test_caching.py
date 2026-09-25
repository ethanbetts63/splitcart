"""The whole-site page cache is not installed, and must not come back.

`UpdateCacheMiddleware`/`FetchFromCacheMiddleware` key a cached 200 on the URL
plus the response's `Vary` headers. Token authentication never touches the
session, so Django never adds `Vary: Cookie`, and every caller -- signed in as
anyone, or signed in as nobody -- computes the same key.

While they were installed this served one shopper's cart, by name and with its
contents, to whoever asked next, and one account's email address to everyone.
The affected views now carry `never_cache`, but that only covers the views
somebody remembered. Removing the middleware is what makes the next per-caller
GET safe by default, and this test is what keeps it removed.

Caching public read-only endpoints is still right, and still happens -- per view,
with `@cache_page`, applied deliberately to answers that do not depend on who is
asking.
"""

import pytest
from django.conf import settings


WHOLE_SITE_CACHE_MIDDLEWARE = (
    "django.middleware.cache.UpdateCacheMiddleware",
    "django.middleware.cache.FetchFromCacheMiddleware",
)


@pytest.mark.parametrize("middleware", WHOLE_SITE_CACHE_MIDDLEWARE)
def test_whole_site_cache_middleware_is_not_installed(middleware):
    assert middleware not in settings.MIDDLEWARE, (
        f"{middleware} caches responses under a key that ignores who is asking, "
        "because token auth never sets Vary: Cookie. It leaked carts and email "
        "addresses between users. Cache per view with @cache_page instead."
    )


def test_throttle_counters_do_not_share_the_page_cache():
    """Throttling needs a cache that page traffic cannot evict.

    The default cache caps at 1000 entries; a burst of page traffic sharing it
    would evict an attacker's attempt count and reset the limit.
    """
    assert "throttling" in settings.CACHES
    assert settings.CACHES["throttling"]["LOCATION"] != settings.CACHES["default"]["LOCATION"]
