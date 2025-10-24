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
from .views.cart_export_view import DownloadShoppingListView, EmailShoppingListView
from .views.store_list_view import StoreListView
from .views.scheduler_view import SchedulerView
from .views.postcode_search_view import PostcodeSearchView
from .views.category_product_list_view import CategoryProductListView
from .views.popular_category_list_view import PopularCategoryListView
from .views.faq_list_view import FaqListView
from .views.product_substitute_list_view import ProductSubstituteListView

from .views.store_list_views import SelectedStoreListListCreateView, SelectedStoreListRetrieveUpdateDestroyView
from .views.cart_views import (
    CartListCreateView,
    CartRetrieveUpdateDestroyView,
    ActiveCartDetailView,
    SwitchActiveCartView,
    RenameCartView,
    ActiveCartItemListCreateView,
    ActiveCartItemUpdateDestroyView,
)
from .views.anonymous_user_view import AnonymousUserCreateView

urlpatterns = [
    path('scheduler/next-candidate/', SchedulerView.as_view(), name='scheduler-next-candidate'),
    path('upload/products/', ProductFileUploadView.as_view(), name='product-file-upload'),
    path('upload/gs1/', Gs1FileUploadView.as_view(), name='gs1-file-upload'),
    path('upload/stores/', StoreFileUploadView.as_view(), name='store-file-upload'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/bargains/', BargainListView.as_view(), name='bargain-product-list'),
    path('products/by-category/', CategoryProductListView.as_view(), name='product-list-by-category'),
    path('categories/popular/', PopularCategoryListView.as_view(), name='popular-category-list'),
    path('faqs/', FaqListView.as_view(), name='faq-list'),
    path('products/<int:product_id>/substitutes/', ProductSubstituteListView.as_view(), name='product-substitute-list'),
    path('files/product_translations/', ProductTranslationFileView.as_view(), name='product-translation-file'),
    path('files/brand_translations/', BrandTranslationFileView.as_view(), name='brand-translation-file'),
    path('products/barcodes/', ProductBarcodeView.as_view(), name='product-barcodes'),
    path('cart/split/', CartOptimizationView.as_view(), name='cart-optimization'),
    path('cart/download-list/', DownloadShoppingListView.as_view(), name='download-shopping-list'),
    path('cart/email-list/', EmailShoppingListView.as_view(), name='email-shopping-list'),
    path('stores/nearby/', StoreListView.as_view(), name='store-list'),
    path('postcodes/search/', PostcodeSearchView.as_view(), name='postcode-search'),

    # SelectedStoreList URLs
    path('store-lists/', SelectedStoreListListCreateView.as_view(), name='store-list-list-create'),
    path('store-lists/<uuid:pk>/', SelectedStoreListRetrieveUpdateDestroyView.as_view(), name='store-list-retrieve-update-destroy'),

    # Cart URLs
    path('carts/', CartListCreateView.as_view(), name='cart-list-create'),
    path('carts/active/', ActiveCartDetailView.as_view(), name='active-cart-detail'),
    path('carts/switch-active/', SwitchActiveCartView.as_view(), name='switch-active-cart'),
    path('carts/rename/', RenameCartView.as_view(), name='rename-cart'),
    path('carts/<uuid:pk>/', CartRetrieveUpdateDestroyView.as_view(), name='cart-retrieve-update-destroy'),

    # CartItem URLs (for the active cart)
    path('carts/active/items/', ActiveCartItemListCreateView.as_view(), name='active-cart-item-list-create'),
    path('carts/active/items/<uuid:pk>/', ActiveCartItemUpdateDestroyView.as_view(), name='active-cart-item-update-destroy'),

    # Anonymous User URLs
    path('anonymous-user/', AnonymousUserCreateView.as_view(), name='anonymous-user-create'),
]
