from django.urls import path
from products.views.api import (
    ProductListView,
    ProductDetailView,
    ProductSearchView,
    ProductSubstitutionView,
    BargainView,
    BargainStatisticsView,
)

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/search/', ProductSearchView.as_view(), name='product-search'),
    path('products/<int:pk>/substitutions/', ProductSubstitutionView.as_view(), name='product-substitutions'),
    path('bargains/', BargainView.as_view(), name='bargain-list'),
    path('bargain-stats/', BargainStatisticsView.as_view(), name='bargain-stats'),
]
