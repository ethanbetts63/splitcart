from django.urls import path
from companies.views.company_list_view import CompanyListView
from companies.views.nearby_store_list_view import StoreListView
from companies.views.postcode_search_view import PostcodeSearchView

urlpatterns = [
    path('companies/', CompanyListView.as_view(), name='company-list'),
    path('stores/', StoreListView.as_view(), name='store-list'),
    path('postcode/geocode/', PostcodeSearchView.as_view(), name='postcode-geocode'),
]
