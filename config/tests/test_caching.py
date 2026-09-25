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

`NoCacheApiMiddleware` covers the gap that leaves. Per-view decoration only
protects the views somebody remembered, and section 7 of
../../../freetheplatform/_docs/security-standard.md exists because the view
somebody forgets is the one that leaks. The middleware gives an `/api/` response
`no-store` when it carries no `Cache-Control` at all, and leaves a response that
already decided exactly as it is -- so `@cache_page` keeps its `max-age`, and a
new per-caller view that forgets `never_cache` is safe rather than silently
cached by whatever sits in front of it.

Both directions are asserted, because both are ways this goes wrong. If the
deferral broke, the six public catalogue views would quietly stop being cached
and every price page would hit the database again. If the scope widened past
`/api/`, the `/pillar-pages/` permanent redirect -- deliberately cacheable
forever, carrying nobody's data -- would become uncacheable.
"""

import pytest
from django.conf import settings
from django.urls import reverse


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


@pytest.mark.django_db
def test_an_api_view_that_sets_no_cache_control_gets_no_store(client):
    """`api/export/companies/` decorates nothing, and returns internal data.

    It is the live example of the view the standard is about: no `never_cache`,
    no `@cache_page`, an internal export behind an API key. Before the
    middleware its response said nothing about caching at all, which reads
    identically to a view that was considered and found safe.
    """
    response = client.get(reverse('export-companies'))

    # `private` as well as `no-store`: a shared cache in front of the API must
    # not hold one caller's response and hand it to the next.
    assert response['Cache-Control'] == 'no-store, private'


@pytest.mark.django_db
def test_a_cache_page_view_keeps_its_max_age(client):
    """The middleware must not delete a deliberate cache.

    `PrimaryCategoryListView` carries `@cache_page(60 * 60 * 24)` because the
    category list is the same for everybody. An unconditional `no-store` -- the
    shape allbikes and bloomprint use, where nothing is cached -- would strip
    that and send every catalogue page back to the database.
    """
    response = client.get(reverse('primary-category-list'))

    assert response.status_code == 200, response.content
    assert 'max-age=86400' in response['Cache-Control']
    assert 'no-store' not in response['Cache-Control']


@pytest.mark.django_db
def test_a_never_cache_view_is_left_exactly_as_it_was(client):
    """A view that already said `no-store` is not rewritten by a weaker string.

    `never_cache` emits `max-age=0, no-cache, no-store, must-revalidate,
    private`. Replacing that with a bare `no-store, private` would drop
    `no-cache` and `must-revalidate`, so the middleware has to leave it alone
    rather than overwrite it with its own value.
    """
    response = client.get(reverse('rest_user_details'))

    directives = {part.strip() for part in response['Cache-Control'].split(',')}
    assert {'no-cache', 'no-store', 'must-revalidate', 'private'} <= directives


@pytest.mark.django_db
def test_paths_outside_api_are_untouched(client):
    """The rule is scoped to `/api/`, and that scope is the point.

    `/pillar-pages/<slug>/` is a permanent redirect kept for old inbound links.
    It carries no caller's data and is meant to be cached indefinitely. A
    site-wide `no-store` would make every one of them a fresh round trip for no
    security gain.
    """
    response = client.get('/pillar-pages/pantry/')

    assert response.status_code == 301
    assert not response.has_header('Cache-Control')
