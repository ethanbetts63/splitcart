from django.urls import path
from .views.product_file_upload_view import ProductFileUploadView

urlpatterns = [
    path('upload/products/', ProductFileUploadView.as_view(), name='product-file-upload'),
]
