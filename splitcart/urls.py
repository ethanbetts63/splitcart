from django.contrib import admin
from django.urls import include, path, re_path
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponsePermanentRedirect
from splitcart.sitemaps import StaticViewSitemap, CategoryPageSitemap
from data_management.views.react_app_view import ReactAppView

sitemaps = {
    'static': StaticViewSitemap,
    'categories': CategoryPageSitemap,
}

# Map old pillar-page slugs that differ from current /categories/ slugs
_PILLAR_SLUG_MAP = {
    'eggs-and-dairy': 'dairy-and-eggs',
    'eggs': 'dairy-and-eggs',
    'pet-and-baby': 'baby',
    'fruit-veg-and-spices': 'fruit-and-veg',
}

def pillar_page_redirect(request, slug):
    new_slug = _PILLAR_SLUG_MAP.get(slug, slug)
    return HttpResponsePermanentRedirect(f'/categories/{new_slug}/')

urlpatterns = [
    path("__debug__/", include("debug_toolbar.urls")),
    path("admin/", admin.site.urls),
    path("api/", include("products.urls")),
    path("api/", include("companies.urls")),
    path("api/", include("users.urls")),
    path("api/", include("data_management.urls")),
    path("sitemap.xml", sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path("pillar-pages/<slug:slug>/", pillar_page_redirect),
    re_path(r'^.*', ReactAppView.as_view(), name='react_app'),
]
