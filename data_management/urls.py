from django.urls import path
from data_management.views.product_file_upload_view import ProductFileUploadView
from data_management.views.category_links_file_upload_view import CategoryLinksFileUploadView
from data_management.views.gs1_file_upload_view import Gs1FileUploadView
from data_management.views.import_semantic_data_view import ImportSemanticDataView

urlpatterns = [
    path('upload/products/', ProductFileUploadView.as_view(), name='upload-products'),
    path('upload/category-links/', CategoryLinksFileUploadView.as_view(), name='upload-category-links'),
    path('upload/gs1/', Gs1FileUploadView.as_view(), name='upload-gs1'),
    path('import/semantic-data/', ImportSemanticDataView.as_view(), name='import-semantic-data'),
]