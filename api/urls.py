from django.urls import path
from .views.product_file_upload_view import ProductFileUploadView
from .views.gs1_file_upload_view import Gs1FileUploadView

from .views.gs1_file_upload_view import Gs1FileUploadView

urlpatterns = [
    path('upload/products/', ProductFileUploadView.as_view(), name='product-file-upload'),
    path('upload/gs1/', Gs1FileUploadView.as_view(), name='gs1-file-upload'),
]
