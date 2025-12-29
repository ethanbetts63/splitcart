from django.urls import path
from products.views.product_list_view import ProductListView
from products.views.product_detail_view import ProductDetailView
from products.views.product_substitute_list_view import ProductSubstituteListView
from products.views.bargain_carousel_view import BargainCarouselView as BargainView
from products.views.bargain_stats_view import BargainStatsView

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:pk>/substitutions/', ProductSubstituteListView.as_view(), name='product-substitutions'),
    path('bargains/', BargainView.as_view(), name='bargain-list'),
    path('bargain-stats/', BargainStatsView.as_view(), name='bargain-stats'),
]
