from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic.base import TemplateView
from django.contrib.sitemaps.views import sitemap
from splitcart.sitemaps import StaticViewSitemap, CategoryPageSitemap
from data_management.views.pillar_page_view import PillarPageView
from products.views.primary_category_list_view import PrimaryCategoryListView
from data_management.views.react_app_view import ReactAppView

sitemaps = {
    'static': StaticViewSitemap,
    'categories': CategoryPageSitemap,
}

urlpatterns = [
    path("__debug__/", include("debug_toolbar.urls")),
    path("admin/", admin.site.urls),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),

    path("api/", include("products.urls")),
    path("api/", include("companies.urls")),
    path("api/", include("users.urls")),
    path("api/", include("data_management.urls")),
    path('api/pillar-pages/<slug:slug>/', PillarPageView.as_view(), name='pillar-page-detail'),
    path('api/primary-categories/', PrimaryCategoryListView.as_view(), name='primary-category-list'),

    path("sitemap.xml", sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    re_path(r'^.*', ReactAppView.as_view(), name='react_app'),
]
