from django.urls import path
from .views.product_file_upload_view import ProductFileUploadView
from .views.gs1_file_upload_view import Gs1FileUploadView
from .views.store_file_upload_view import StoreFileUploadView
from .views.product_list_view import ProductListView
from .views.bargain_list_view import BargainListView # Import the new view
from .views.product_translation_file_view import ProductTranslationFileView
from .views.brand_translation_file_view import BrandTranslationFileView
from .views.product_barcode_view import ProductBarcodeView
from .views.cart_optimization_view import CartOptimizationView
from .views.store_list_view import StoreListView
from .views.scheduler_view import SchedulerView

from .views.product_substitute_list_view import ProductSubstituteListView

urlpatterns = [
    path('scheduler/next-candidate/', SchedulerView.as_view(), name='scheduler-next-candidate'),
    path('upload/products/', ProductFileUploadView.as_view(), name='product-file-upload'),
    path('upload/gs1/', Gs1FileUploadView.as_view(), name='gs1-file-upload'),
    path('upload/stores/', StoreFileUploadView.as_view(), name='store-file-upload'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/bargains/', BargainListView.as_view(), name='bargain-product-list'),
    path('products/<int:product_id>/substitutes/', ProductSubstituteListView.as_view(), name='product-substitute-list'),
    path('files/product_translations/', ProductTranslationFileView.as_view(), name='product-translation-file'),
    path('files/brand_translations/', BrandTranslationFileView.as_view(), name='brand-translation-file'),
    path('products/barcodes/', ProductBarcodeView.as_view(), name='product-barcodes'),
    path('cart/split/', CartOptimizationView.as_view(), name='cart-optimization'),
    path('stores/nearby/', StoreListView.as_view(), name='store-list'),
]
