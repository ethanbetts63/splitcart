"""The callables `freetheplatform.auth` calls when it has something to send.

The package counts, decides and hands over; the site sends. Wording, recipients
and the frontend's own URL are the site's.

Mail goes through Django's own `send_mail` and the SMTP settings in
`config.settings`. Every failure is logged and swallowed: these run inside a
failed login or a reset request, and an unreachable mail server must turn
neither into a 500 -- for a reset, a different answer would also say whether the
address has an account.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def notify_account_security(event, user, state, request=None):
    """Tell the operator an account is being guessed at, or has locked.

    The package calls this after five consecutive failures and again on the
    lock, at most once an hour per account.
    """
    logger.warning("auth %s for user %s (%s failures)", event, user.pk, state.failure_count)

    subject = {
        "repeated_failures": f"SplitCart: repeated failed sign-ins for {user.email}",
        "locked": f"SplitCart: account locked: {user.email}",
    }.get(event, f"SplitCart: account security event for {user.email}")
    body = (
        f"Event: {event}\n"
        f"Account: {user.email} (id {user.pk})\n"
        f"Consecutive failures: {state.failure_count}\n"
        f"Locked until: {getattr(state, 'locked_until', None)}\n"
    )
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.ADMIN_EMAIL])
    except Exception:
        logger.exception("Account security alert failed for user id=%s.", user.pk)


def send_password_reset(user, uid, token, request=None):
    """Mail the reset link. The page it opens is `frontend/src/app/reset-password/`."""
    link = f"{settings.SITE_URL}/reset-password/{uid}/{token}/"
    body = (
        "Someone asked to reset the password for your SplitCart account.\n\n"
        f"Choose a new one here:\n{link}\n\n"
        "The link works once and expires in three days. If it was not you, "
        "ignore this email and your password stays as it is.\n"
    )
    try:
        send_mail("Reset your SplitCart password", body, settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception:
        logger.exception("Password reset email failed for user id=%s.", user.pk)
