from django.contrib import admin
from django.urls import include, path, re_path
from django.contrib.sitemaps.views import sitemap
from splitcart.sitemaps import StaticViewSitemap, CategoryPageSitemap
from data_management.views.react_app_view import ReactAppView

sitemaps = {
    'static': StaticViewSitemap,
    'categories': CategoryPageSitemap,
}

urlpatterns = [
    path("__debug__/", include("debug_toolbar.urls")),
    path("admin/", admin.site.urls),
    path("api/", include("products.urls")),
    path("api/", include("companies.urls")),
    path("api/", include("users.urls")),
    path("api/", include("data_management.urls")),
    path("sitemap.xml", sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    re_path(r'^.*', ReactAppView.as_view(), name='react_app'),
]
