"""`POST /api/auth/password/reset/` -- live, unauthenticated, and broken.

The route is real: `users/urls.py` shadows dj-rest-auth's view to give it a
`password_reset` throttle scope, and anyone may call it. It cannot succeed.

Two faults stacked on the same path:

1. `dj_rest_auth.forms.AllAuthPasswordResetForm` builds the link in the email by
   calling `reverse('password_reset_confirm')` -- allauth's own URL name.
   Nothing here routes it. `users/urls.py` registers dj-rest-auth's
   `rest_password_reset_confirm` instead, which is a different name, so the
   reverse raises `NoReverseMatch` and the request answers **500**.
2. If it got past that, `users/adapter.CustomAccountAdapter.send_mail` renders
   `<prefix>_message.html` unconditionally. allauth ships only the `.txt` forms
   of its account emails and this repository has no `templates/` directory at
   all, so the next step is `TemplateDoesNotExist` -- another 500.

Underneath both is a product gap: the reset link has to land on a page that
takes a new password, and the frontend has no such route. Password reset was
never finished, and the endpoint was left routed.

The test below asserts what the endpoint is supposed to do. It is marked
`xfail(strict=True)`, so it stays quiet while the defect stands and fails loudly
the day someone fixes it without deleting this note. It is not marked `skip`:
the assertion is the record of what is owed.
"""

import pytest
from django.core import mail
from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.xfail(
    strict=True,
    reason=(
        "NoReverseMatch for 'password_reset_confirm' -- the reset link has no "
        "route to point at, and no frontend page to land on. See this module's "
        "docstring."
    ),
)
def test_a_reset_request_sends_the_account_a_link(api_client, user):
    response = api_client.post(
        reverse('rest_password_reset'), {'email': user.email}, format='json'
    )

    assert response.status_code == 200, response.content
    assert [message.to for message in mail.outbox] == [[user.email]]


@pytest.mark.django_db
def test_an_unknown_email_is_not_confirmed_or_denied(api_client):
    """Whatever the endpoint ends up doing, it must not become an oracle for
    which addresses hold accounts. allauth's form silently succeeds for an
    unknown address, and that half does work today."""
    response = api_client.post(
        reverse('rest_password_reset'),
        {'email': 'nobody@example.com'},
        format='json',
    )

    assert response.status_code == 200, response.content
    assert mail.outbox == []
