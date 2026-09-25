from django.urls import path, include, re_path
from rest_framework.routers import SimpleRouter

from users.views.cart_viewset import CartViewSet
from users.views.auth_views import (
    ThrottledLoginView,
    ThrottledLogoutView,
    ThrottledPasswordChangeView,
    ThrottledPasswordResetConfirmView,
    ThrottledPasswordResetView,
    ThrottledRegisterView,
    ThrottledResendEmailVerificationView,
    ThrottledUserDetailsView,
    ThrottledVerifyEmailView,
)

router = SimpleRouter()
router.register(r'carts', CartViewSet, basename='cart')

# dj_rest_auth routes its own views from an include, so the only way to give a
# credential endpoint a throttle scope is to shadow it. These use the same
# optional-trailing-slash patterns dj_rest_auth itself uses, and sit before the
# includes, so every URL and every reverse() name stays exactly where it was
# while resolution reaches the scoped subclass -- including the no-slash form,
# which a `path()` would have missed and left on the library's own view.
urlpatterns = [
    path('', include(router.urls)),

    re_path(r'^auth/login/?$', ThrottledLoginView.as_view(), name='rest_login'),
    re_path(r'^auth/logout/?$', ThrottledLogoutView.as_view(), name='rest_logout'),
    re_path(r'^auth/user/?$', ThrottledUserDetailsView.as_view(), name='rest_user_details'),
    re_path(
        r'^auth/password/reset/?$',
        ThrottledPasswordResetView.as_view(),
        name='rest_password_reset',
    ),
    re_path(
        r'^auth/password/reset/confirm/?$',
        ThrottledPasswordResetConfirmView.as_view(),
        name='rest_password_reset_confirm',
    ),
    re_path(
        r'^auth/password/change/?$',
        ThrottledPasswordChangeView.as_view(),
        name='rest_password_change',
    ),
    path('auth/', include('dj_rest_auth.urls')),

    re_path(r'^auth/registration/$', ThrottledRegisterView.as_view(), name='rest_register'),
    re_path(
        r'^auth/registration/verify-email/?$',
        ThrottledVerifyEmailView.as_view(),
        name='rest_verify_email',
    ),
    re_path(
        r'^auth/registration/resend-email/?$',
        ThrottledResendEmailVerificationView.as_view(),
        name='rest_resend_email',
    ),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
]
