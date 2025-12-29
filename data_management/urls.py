from django.urls import path
from data_management.views.api import (
    ProductFileUploadView,
    CategoryLinksFileUploadView,
    Gs1FileUploadView,
    ImportSemanticDataView,
)

urlpatterns = [
    path('upload/products/', ProductFileUploadView.as_view(), name='upload-products'),
    path('upload/category-links/', CategoryLinksFileUploadView.as_view(), name='upload-category-links'),
    path('upload/gs1/', Gs1FileUploadView.as_view(), name='upload-gs1'),
    path('import/semantic-data/', ImportSemanticDataView.as_view(), name='import-semantic-data'),
]