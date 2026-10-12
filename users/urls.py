from django.urls import include, path
from rest_framework.routers import SimpleRouter

from users.views.auth_views import LoginView, RegisterView
from users.views.cart_viewset import CartViewSet

router = SimpleRouter()
router.register(r'carts', CartViewSet, basename='cart')

# Sessions are `freetheplatform.auth`'s, mounted as they come: token/refresh/,
# token/logout/, me/ and password/*. Login is shadowed by splitcart's subclass,
# which sits before the include so `token/` resolves to it -- see
# users/views/auth_views.py for what it adds.
urlpatterns = [
    path('', include(router.urls)),
    path('token/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('', include('freetheplatform.auth.urls')),
]
