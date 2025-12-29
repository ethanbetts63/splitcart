from django.urls import path
from users.views.api import (
    CartOptimizationView,
    ActiveCartDetailView,
    ActiveCartItemListCreateView,
    ActiveCartItemUpdateDestroyView,
    CartListCreateView,
    CartRetrieveUpdateDestroyView,
    CartSubstitutionUpdateDestroyView,
    CartSyncView,
    RenameCartView,
    SwitchActiveCartView,
)

urlpatterns = [
    path('cart/optimize/', CartOptimizationView.as_view(), name='cart-optimize'),
    path('cart/active/', ActiveCartDetailView.as_view(), name='active-cart-detail'),
    path('cart/active/items/', ActiveCartItemListCreateView.as_view(), name='active-cart-items'),
    path('cart/active/items/<int:pk>/', ActiveCartItemUpdateDestroyView.as_view(), name='active-cart-item-detail'),
    path('carts/', CartListCreateView.as_view(), name='cart-list-create'),
    path('carts/<int:pk>/', CartRetrieveUpdateDestroyView.as_view(), name='cart-detail'),
    path('cart-items/<int:cart_item_pk>/substitutions/<int:substitution_pk>/', CartSubstitutionUpdateDestroyView.as_view(), name='cart-substitution-detail'),
    path('cart/sync/', CartSyncView.as_view(), name='cart-sync'),
    path('cart/rename/', RenameCartView.as_view(), name='cart-rename'),
    path('cart/switch-active/', SwitchActiveCartView.as_view(), name='cart-switch-active'),
]
