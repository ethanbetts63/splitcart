"""The two inbox upload endpoints.

`BaseFileUploadView` is the server half of the scrape-to-database lifecycle: the
local machine gzips a `.jsonl` and posts it, and this writes it into an inbox a
management command later reads. It is reachable only with the internal API key,
and it writes to the filesystem, which makes both the gate and the rejected
shapes worth pinning.
"""

import gzip
import io
import json
import os

import pytest
from django.urls import reverse

INTERNAL_KEY = 'test-internal-key'


@pytest.fixture(autouse=True)
def internal_api_key(monkeypatch):
    """`IsInternalAPIRequest` reads the key from the process environment.

    Set here rather than inherited from a developer's `.env`, so the tests say
    the same thing on every machine -- including one where the variable is
    unset, which would otherwise refuse every caller and make the gate look
    airtight for the wrong reason.
    """
    monkeypatch.setenv('INTERNAL_API_KEY', INTERNAL_KEY)


@pytest.fixture(autouse=True)
def inbox_root(settings, tmp_path):
    """Uploads land under `PIPELINE_DATA_DIR`; point it at a temporary tree."""
    settings.PIPELINE_DATA_DIR = tmp_path
    return tmp_path


def _gzipped(name, payload):
    from django.core.files.uploadedfile import SimpleUploadedFile

    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb') as archive:
        archive.write(payload.encode('utf-8'))
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='application/gzip')


UPLOADS = [
    ('product-file-upload', ('inboxes', 'product_inbox'), 'products.jsonl.gz'),
    (
        'category-links-file-upload',
        ('inboxes', 'category_links_inbox'),
        'category_links.json.gz',
    ),
]


@pytest.mark.django_db
@pytest.mark.parametrize('url_name, inbox, file_name', UPLOADS)
class TestUploadEndpoints:
    def test_an_upload_lands_decompressed_in_the_inbox(
        self, api_client, inbox_root, url_name, inbox, file_name
    ):
        body = json.dumps({'name': 'Milk'})

        response = api_client.post(
            reverse(url_name),
            {'file': _gzipped(file_name, body)},
            format='multipart',
            HTTP_X_INTERNAL_API_KEY=INTERNAL_KEY,
        )

        assert response.status_code == 201, response.content
        written = inbox_root.joinpath(*inbox) / file_name.replace('.gz', '')
        assert written.read_text(encoding='utf-8') == body

    def test_without_the_internal_key_nothing_is_written(
        self, api_client, inbox_root, url_name, inbox, file_name
    ):
        response = api_client.post(
            reverse(url_name),
            {'file': _gzipped(file_name, '{}')},
            format='multipart',
        )

        # 401 or 403 depending on whether DRF offers a challenge header; both
        # are "denied", and which one is DRF's business rather than this view's.
        assert response.status_code in (401, 403)
        assert not inbox_root.joinpath(*inbox).exists()

    def test_the_wrong_internal_key_is_refused(
        self, api_client, url_name, inbox, file_name
    ):
        response = api_client.post(
            reverse(url_name),
            {'file': _gzipped(file_name, '{}')},
            format='multipart',
            HTTP_X_INTERNAL_API_KEY='not-the-key',
        )

        assert response.status_code in (401, 403)

    def test_a_request_with_no_file_is_a_bad_request(
        self, api_client, url_name, inbox, file_name
    ):
        response = api_client.post(
            reverse(url_name),
            {},
            format='multipart',
            HTTP_X_INTERNAL_API_KEY=INTERNAL_KEY,
        )

        assert response.status_code == 400
        assert 'File not provided' in response.json()['error']

    def test_an_uncompressed_file_is_refused(
        self, api_client, inbox_root, url_name, inbox, file_name
    ):
        from django.core.files.uploadedfile import SimpleUploadedFile

        response = api_client.post(
            reverse(url_name),
            {'file': SimpleUploadedFile('products.jsonl', b'{}')},
            format='multipart',
            HTTP_X_INTERNAL_API_KEY=INTERNAL_KEY,
        )

        assert response.status_code == 400
        assert 'Invalid file format' in response.json()['error']
        assert not inbox_root.joinpath(*inbox).exists()

    def test_a_file_that_is_not_really_gzip_is_reported_not_raised(
        self, api_client, url_name, inbox, file_name
    ):
        """The name promises gzip; the bytes do not. The view has to answer,
        not raise -- this is an endpoint a scraper retries against."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        response = api_client.post(
            reverse(url_name),
            {'file': SimpleUploadedFile(file_name, b'not gzip at all')},
            format='multipart',
            HTTP_X_INTERNAL_API_KEY=INTERNAL_KEY,
        )

        assert response.status_code == 500
        assert 'Failed to process file' in response.json()['error']


@pytest.mark.django_db
class TestInboxSeparation:
    def test_each_endpoint_writes_to_its_own_inbox(self, api_client, inbox_root):
        """The inbox is the only thing telling the update command what a file
        is, so a product file in the category-links inbox is a silent misread."""
        api_client.post(
            reverse('product-file-upload'),
            {'file': _gzipped('products.jsonl.gz', '{}')},
            format='multipart',
            HTTP_X_INTERNAL_API_KEY=INTERNAL_KEY,
        )

        assert os.listdir(inbox_root / 'inboxes' / 'product_inbox') == ['products.jsonl']
        assert not (inbox_root / 'inboxes' / 'category_links_inbox').exists()
