from django.urls import path, include
from rest_framework_nested import routers

from users.views.cart_viewset import CartViewSet
from users.views.selected_store_list_viewset import SelectedStoreListViewSet
from users.views.cart_item_viewset import CartItemViewSet
from users.views.cart_substitution_viewset import CartSubstitutionViewSet
from .views.nearby_store_list_view import NearbyStoreListView

# The main router includes the top-level resources
router = routers.SimpleRouter()
router.register(r'carts', CartViewSet, basename='cart')
router.register(r'store-lists', SelectedStoreListViewSet, basename='storelist')

# A nested router for items within a cart
# This creates URLs like /carts/{cart_pk}/items/
carts_router = routers.NestedSimpleRouter(router, r'carts', lookup='cart')
carts_router.register(r'items', CartItemViewSet, basename='cart-items')

# A nested router for substitutions within a cart item
# This creates URLs like /carts/{cart_pk}/items/{item_pk}/substitutions/
cart_items_router = routers.NestedSimpleRouter(carts_router, r'items', lookup='item')
cart_items_router.register(r'substitutions', CartSubstitutionViewSet, basename='cart-substitution') # Register the new ViewSet

urlpatterns = [
    path('', include(router.urls)),
    path('', include(carts_router.urls)),
    path('', include(cart_items_router.urls)), 
    path('stores/nearby/', NearbyStoreListView.as_view(), name='store-list'),
]
