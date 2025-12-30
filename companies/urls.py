from django.urls import path
from .views.export_anchor_stores_view import ExportAnchorStoresView
from .views.export_stores_view import ExportStoresView
from .views.company_list_view import CompanyListView
from .views.postcode_search_view import PostcodeSearchView

urlpatterns = [
    path('export/anchor-stores/', ExportAnchorStoresView.as_view(), name='export-anchor-stores'),
    path('export/stores/', ExportStoresView.as_view(), name='export-stores'),
    path('export/companies/', CompanyListView.as_view(), name='export-companies'),
    path('postcodes/search/', PostcodeSearchView.as_view(), name='postcode-search'),
]
