"""Throttled subclasses of dj_rest_auth's views.

dj_rest_auth ships its own views and routes them from an include, so there is
nowhere to declare a throttle scope on them except a subclass. Without these,
every credential endpoint on the site fell through to the catch-all `anon` rate
-- 5000 a day, one attempt every seventeen seconds, with no account lockout
behind it. Removing the catch-all (see `config.settings`) would otherwise leave
them with no limit at all.

Behaviour is unchanged: each class adds a scope and nothing else.
"""

from dj_rest_auth.registration.views import (
    RegisterView,
    ResendEmailVerificationView,
    VerifyEmailView,
)
from dj_rest_auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
    UserDetailsView,
)


class ThrottledLoginView(LoginView):
    throttle_scope = 'login'


class ThrottledRegisterView(RegisterView):
    throttle_scope = 'register'


class ThrottledPasswordResetView(PasswordResetView):
    throttle_scope = 'password_reset'


class ThrottledPasswordResetConfirmView(PasswordResetConfirmView):
    throttle_scope = 'password_reset'


class ThrottledPasswordChangeView(PasswordChangeView):
    throttle_scope = 'password_change'


class ThrottledLogoutView(LogoutView):
    throttle_scope = 'session'


class ThrottledUserDetailsView(UserDetailsView):
    throttle_scope = 'session'


class ThrottledVerifyEmailView(VerifyEmailView):
    throttle_scope = 'register'


class ThrottledResendEmailVerificationView(ResendEmailVerificationView):
    # Each accepted request sends an email to an address the caller chose.
    throttle_scope = 'register'
