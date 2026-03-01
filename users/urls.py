from django.urls import path, include
from rest_framework.routers import SimpleRouter

from users.views.cart_viewset import CartViewSet
from users.views.selected_store_list_viewset import SelectedStoreListViewSet
from .views.nearby_store_list_view import NearbyStoreListView

router = SimpleRouter()
router.register(r'carts', CartViewSet, basename='cart')
router.register(r'store-lists', SelectedStoreListViewSet, basename='storelist')

urlpatterns = [
    path('', include(router.urls)),
    path('stores/nearby/', NearbyStoreListView.as_view(), name='store-list'),
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
]
