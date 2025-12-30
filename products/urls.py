from django.urls import path
from .views.product_list_view import ProductListView
from .views.bargain_carousel_view import BargainCarouselView
from .views.product_detail_view import ProductDetailView
from .views.primary_category_list_view import PrimaryCategoryListView
from .views.bargain_stats_view import BargainStatsView
from .views.product_substitute_list_view import ProductSubstituteListView
from .views.product_barcode_view import ProductBarcodeView
from .views.export_categories_view import ExportCategoriesView, ExportCategoriesWithProductsView
from .views.export_category_links_view import ExportCategoryLinksView
from .views.export_prices_view import ExportPricesView
from .views.export_products_view import ExportProductsView
from .views.substitutions_file_upload_view import SubstitutionsFileUploadView

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/bargain-carousel/', BargainCarouselView.as_view(), name='bargain-carousel'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('categories/primary/', PrimaryCategoryListView.as_view(), name='primary-category-list'),
    path('stats/bargains/', BargainStatsView.as_view(), name='bargain-stats'),
    path('products/<int:product_id>/substitutes/', ProductSubstituteListView.as_view(), name='product-substitute-list'),
    path('products/barcodes/', ProductBarcodeView.as_view(), name='product-barcodes'),
    path('export/categories/', ExportCategoriesView.as_view(), name='export-categories'),
    path('export/categories-with-products/', ExportCategoriesWithProductsView.as_view(), name='export-categories-with-products'),
    path('export/category_links/', ExportCategoryLinksView.as_view(), name='export-category-links'),
    path('export/prices/', ExportPricesView.as_view(), name='export-prices'),
    path('export/products/', ExportProductsView.as_view(), name='export-products'),
    path('upload/substitutions/', SubstitutionsFileUploadView.as_view(), name='substitutions-file-upload'),
]
