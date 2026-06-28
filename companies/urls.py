from django.urls import path
from .views.company_list_view import CompanyListView
from .views.postcode_search_view import PostcodeSearchView

urlpatterns = [
    path('export/companies/', CompanyListView.as_view(), name='export-companies'),
    path('postcodes/search/', PostcodeSearchView.as_view(), name='postcode-search'),
]
