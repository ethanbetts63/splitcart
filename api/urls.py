from django.urls import path
from .views.product_file_upload_view import ProductFileUploadView
from .views.gs1_file_upload_view import Gs1FileUploadView
from .views.store_file_upload_view import StoreFileUploadView
from .views.category_links_file_upload_view import CategoryLinksFileUploadView
from .views.substitutions_file_upload_view import SubstitutionsFileUploadView
from .views.bargains_file_upload_view import BargainsFileUploadView
from .views.frontend_views.product_list_view import ProductListView
from .views.frontend_views.bargain_list_view import BargainListView # Import the new view
from .views.product_translation_file_view import ProductTranslationFileView
from .views.brand_translation_file_view import BrandTranslationFileView
from .views.product_barcode_view import ProductBarcodeView
from .views.frontend_views.cart_optimization_view import CartOptimizationView
from .views.frontend_views.cart_export_view import DownloadShoppingListView, EmailShoppingListView
from .views.scheduler_view import SchedulerView
from .views.frontend_views.postcode_search_view import PostcodeSearchView
from .views.category_product_list_view import CategoryProductListView
from .views.frontend_views.popular_category_list_view import PopularCategoryListView
from .views.frontend_views.faq_list_view import FaqListView
from .views.frontend_views.product_substitute_list_view import ProductSubstituteListView
from .views.frontend_views.store_list_views.nearby_store_list_view import StoreListView
from .views.frontend_views.store_list_views.list_create_view import SelectedStoreListCreateView
from .views.frontend_views.store_list_views.retrieve_update_destroy_view import SelectedStoreListRetrieveUpdateDestroyView
from .views.frontend_views.cart_views import (
    CartListCreateView,
    CartRetrieveUpdateDestroyView,
    ActiveCartDetailView,
    SwitchActiveCartView,
    RenameCartView,
    ActiveCartItemListCreateView,
    ActiveCartItemUpdateDestroyView,
    CartSubstitutionUpdateDestroyView,
    CartSyncView,
)
from .views.frontend_views.initial_setup_view import InitialSetupView
from .views.export_categories_view import ExportCategoriesView, ExportCategoriesWithProductsView
from .views.export_products_view import ExportProductsView
from .views.export_prices_view import ExportPricesView
from .views.export_category_links_view import ExportCategoryLinksView
from .views.export_stores_view import ExportStoresView
from .views.import_semantic_data_view import ImportSemanticDataView

urlpatterns = [
    path('initial-setup/', InitialSetupView.as_view(), name='initial-setup'),
    path('scheduler/next-candidate/', SchedulerView.as_view(), name='scheduler-next-candidate'),
    path('upload/products/', ProductFileUploadView.as_view(), name='product-file-upload'),
    path('upload/gs1/', Gs1FileUploadView.as_view(), name='gs1-file-upload'),
    path('upload/stores/', StoreFileUploadView.as_view(), name='store-file-upload'),
    path('upload/category-links/', CategoryLinksFileUploadView.as_view(), name='category-links-file-upload'),
    path('upload/substitutions/', SubstitutionsFileUploadView.as_view(), name='substitutions-file-upload'),
    path('upload/bargains/', BargainsFileUploadView.as_view(), name='bargains-file-upload'),
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
    path('export/categories/', ExportCategoriesView.as_view(), name='export-categories'),
    path('export/categories-with-products/', ExportCategoriesWithProductsView.as_view(), name='export-categories-with-products'),
    path('export/products/', ExportProductsView.as_view(), name='export-products'),
    path('export/prices/', ExportPricesView.as_view(), name='export-prices'),
    path('export/category_links/', ExportCategoryLinksView.as_view(), name='export-category-links'),
    path('export/stores/', ExportStoresView.as_view(), name='export-stores'),
    path('import/semantic_data/', ImportSemanticDataView.as_view(), name='import-semantic-data'),

    # SelectedStoreList URLs
    path('store-lists/', SelectedStoreListCreateView.as_view(), name='store-list-list-create'),
    path('store-lists/<uuid:pk>/', SelectedStoreListRetrieveUpdateDestroyView.as_view(), name='store-list-retrieve-update-destroy'),

    # Cart URLs
    path('carts/', CartListCreateView.as_view(), name='cart-list-create'),
    path('carts/sync/', CartSyncView.as_view(), name='cart-sync'),
    path('carts/active/', ActiveCartDetailView.as_view(), name='active-cart-detail'),
    path('carts/switch-active/', SwitchActiveCartView.as_view(), name='switch-active-cart'),
    path('carts/rename/', RenameCartView.as_view(), name='rename-cart'),
    path('carts/<uuid:pk>/', CartRetrieveUpdateDestroyView.as_view(), name='cart-retrieve-update-destroy'),

    # CartItem URLs (for the active cart)
    path('carts/active/items/', ActiveCartItemListCreateView.as_view(), name='active-cart-item-list-create'),
    path('carts/active/items/<uuid:pk>/', ActiveCartItemUpdateDestroyView.as_view(), name='active-cart-item-update-destroy'),
    path('carts/active/items/<uuid:cart_item_pk>/substitutions/<uuid:substitution_pk>/', CartSubstitutionUpdateDestroyView.as_view(), name='cart-substitution-update-destroy'),
]
