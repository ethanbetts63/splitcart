from django.urls import path
from .views.company_list_view import CompanyListView

urlpatterns = [
    path('export/companies/', CompanyListView.as_view(), name='export-companies'),
]
