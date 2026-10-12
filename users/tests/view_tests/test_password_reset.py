"""`POST /api/password/reset/` and `.../confirm/` -- the package's views, splitcart's email.

What is splitcart's is `users.notifications.send_password_reset`: the wording,
and the link, which has to land on `frontend/src/app/reset-password/`.
"""

import re

import pytest
from django.core import mail
from django.urls import reverse

from users.tests.factories import TEST_PASSWORD

NEW_PASSWORD = 'plausible-replacement-91'


def _request_reset(client, email):
    return client.post(reverse('ftp_auth:password-reset'), {'email': email}, format='json')


def _link_parts():
    (message,) = mail.outbox
    match = re.search(r'/reset-password/([^/\s]+)/([^/\s]+)/', message.body)
    assert match, message.body
    return match.group(1), match.group(2)


@pytest.mark.django_db
class TestRequestingAReset:
    def test_a_reset_request_sends_the_account_a_link_to_the_reset_page(self, api_client, user, settings):
        response = _request_reset(api_client, user.email)

        assert response.status_code == 200, response.content
        assert [message.to for message in mail.outbox] == [[user.email]]
        assert f'{settings.SITE_URL}/reset-password/' in mail.outbox[0].body

    def test_an_unknown_email_is_not_confirmed_or_denied(self, api_client, user):
        known = _request_reset(api_client, user.email)
        unknown = _request_reset(api_client, 'nobody@example.com')

        assert known.status_code == unknown.status_code == 200
        assert known.json() == unknown.json()
        assert len(mail.outbox) == 1

    def test_a_mail_server_that_is_down_changes_nothing_the_caller_sees(
        self, api_client, user, monkeypatch
    ):
        def fails(*args, **kwargs):
            raise OSError('smtp.gmail.com refused the connection')

        monkeypatch.setattr('users.notifications.send_mail', fails)

        response = _request_reset(api_client, user.email)

        assert response.status_code == 200, response.content


@pytest.mark.django_db
class TestSpendingTheLink:
    def test_the_link_sets_a_new_password(self, api_client, user):
        _request_reset(api_client, user.email)
        uid, token = _link_parts()

        response = api_client.post(
            reverse('ftp_auth:password-reset-confirm'),
            {'uid': uid, 'token': token, 'new_password': NEW_PASSWORD},
            format='json',
        )

        assert response.status_code == 200, response.content
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)

    def test_the_link_works_once(self, api_client, user):
        _request_reset(api_client, user.email)
        uid, token = _link_parts()
        confirm = reverse('ftp_auth:password-reset-confirm')
        api_client.post(confirm, {'uid': uid, 'token': token, 'new_password': NEW_PASSWORD}, format='json')

        again = api_client.post(
            confirm, {'uid': uid, 'token': token, 'new_password': TEST_PASSWORD}, format='json'
        )

        assert again.status_code == 400
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)
