from django.urls import path
from companies.views.api import (
    CompanyListView,
    StoreListView,
    PostcodeGeocodeView,
    StoreGeocodeView,
    StoreByPostcodeView,
    SelectedStoreListView,
    SelectedStoreCreateView,
    SelectedStoreDeleteView,
    ShoppingListStoreView,
)

urlpatterns = [
    path('companies/', CompanyListView.as_view(), name='company-list'),
    path('stores/', StoreListView.as_view(), name='store-list'),
    path('postcode/geocode/', PostcodeGeocodeView.as_view(), name='postcode-geocode'),
    path('stores/geocode/', StoreGeocodeView.as_view(), name='store-geocode'),
    path('stores/by-postcode/', StoreByPostcodeView.as_view(), name='store-by-postcode'),
    path('selected-stores/', SelectedStoreListView.as_view(), name='selected-store-list'),
    path('selected-stores/add/', SelectedStoreCreateView.as_view(), name='selected-store-add'),
    path('selected-stores/delete/', SelectedStoreDeleteView.as_view(), name='selected-store-delete'),
    path('shopping-list-stores/', ShoppingListStoreView.as_view(), name='shopping-list-stores'),
]
