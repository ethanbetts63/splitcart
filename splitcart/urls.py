"""
URL configuration for splitcart project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic.base import TemplateView
from django.contrib.sitemaps.views import sitemap
from api.sitemaps import StaticViewSitemap, PillarPageSitemap
from splitcart.views.api import (
    FaqListView,
    PillarPageView,
    PrimaryCategoryListView,
)
from splitcart.views.react_app_view import ReactAppView

sitemaps = {
    'static': StaticViewSitemap,
    'pillar-pages': PillarPageSitemap,
}

api_urlpatterns = [
    path("", include("products.urls")),
    path("", include("companies.urls")),
    path("", include("users.urls")),
    path("", include("data_management.urls")),
    path('faqs/', FaqListView.as_view(), name='faq-list'),
    path('pillar-pages/<slug:slug>/', PillarPageView.as_view(), name='pillar-page-detail'),
    path('primary-categories/', PrimaryCategoryListView.as_view(), name='primary-category-list'),
]

urlpatterns = [
    path("__debug__/", include("debug_toolbar.urls")),
    path("admin/", admin.site.urls),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path("api/", include(api_urlpatterns)),
    path("data_management/", include("data_management.urls")),
    path("sitemap.xml", sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    re_path(r'^.*', ReactAppView.as_view(), name='react_app'),
]
