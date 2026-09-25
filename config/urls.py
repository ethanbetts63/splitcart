from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.http import HttpResponsePermanentRedirect

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

# Django here is an API and nothing else. There is no catch-all serving a React
# shell: the template it named was never migrated out of frontend/dist, so every
# unrouted path -- every typo, every crawler probe -- raised TemplateDoesNotExist
# and answered 500 where it should have answered 404.
urlpatterns = [
    path("api/", include("products.urls")),
    path("api/", include("companies.urls")),
    path("api/", include("users.urls")),
    path("api/", include("pipeline.urls")),
    path("pillar-pages/<slug:slug>/", pillar_page_redirect),
]

# Development-only routes. The admin reaches every record through the ORM and
# its login is a plain Django view that no DRF throttle touches, so the surface
# is removed in production rather than hardened; staff work is done from a
# manage.py shell. The toolbar's route follows the app that serves it.
if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
        path("admin/", admin.site.urls),
    ]
