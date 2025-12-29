from django.urls import path
from products.views.api import (
    ProductListView,
    ProductDetailView,
    ProductSubstituteListView,
    BargainCarouselView,
    BargainStatsView,
    ProductBarcodeView
)

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:product_id>/substitutes/', ProductSubstituteListView.as_view(), name='product-substitutes'),
    path('bargain-carousel/', BargainCarouselView.as_view(), name='bargain-carousel'),
    path('bargain-stats/', BargainStatsView.as_view(), name='bargain-stats'),
    path('product-barcode/', ProductBarcodeView.as_view(), name='product-barcode'),
]
