from django.urls import path
from users.views.cart_optimization_view import CartOptimizationView
from users.views.active_cart_detail_view import ActiveCartDetailView
from users.views.active_cart_item_list_create_view import ActiveCartItemListCreateView
from users.views.active_cart_item_update_destroy_view import ActiveCartItemUpdateDestroyView
from users.views.cart_list_create_view import CartListCreateView
from users.views.cart_retrieve_update_destroy_view import CartRetrieveUpdateDestroyView
from users.views.cart_substitution_update_destroy_view import CartSubstitutionUpdateDestroyView
from users.views.cart_sync_view import CartSyncView
from users.views.rename_cart_view import RenameCartView
from users.views.switch_active_cart_view import SwitchActiveCartView
from .views.initial_setup_view import InitialSetupView
from .views.nearby_store_list_view import StoreListView
from .views.list_create_view import SelectedStoreListCreateView
from .views.retrieve_update_destroy_view import SelectedStoreListRetrieveUpdateDestroyView

urlpatterns = [
    path('initial-setup/', InitialSetupView.as_view(), name='initial-setup'),
    path('stores/nearby/', StoreListView.as_view(), name='store-list'),
    path('store-lists/', SelectedStoreListCreateView.as_view(), name='store-list-list-create'),
    path('store-lists/<uuid:pk>/', SelectedStoreListRetrieveUpdateDestroyView.as_view(), name='store-list-retrieve-update-destroy'),

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
