from django.urls import path
from companies.views.api import (
    NearbyStoreListView,
    PostcodeSearchView,
    CompanyListView,
)

urlpatterns = [
    path('stores/nearby/', NearbyStoreListView.as_view(), name='nearby-stores'),
    path('postcode-search/', PostcodeSearchView.as_view(), name='postcode-search'),
    path('companies/', CompanyListView.as_view(), name='company-list'),
]
