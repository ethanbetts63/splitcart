from django.urls import path, include
from rest_framework.routers import SimpleRouter

from users.views.cart_viewset import CartViewSet

router = SimpleRouter()
router.register(r'carts', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
]
