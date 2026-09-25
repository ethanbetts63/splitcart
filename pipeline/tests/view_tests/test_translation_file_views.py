"""The two translation-table download endpoints.

The local machine pulls the product and brand translation tables from the server
before it normalises anything, so these are the read half of the internal API.
`BasePythonFileView` serves whatever the generator last wrote to disk and hangs
an ETag off its contents, which is the only thing keeping a scrape run from
re-downloading the same megabyte every time.
"""

import pytest
from django.urls import reverse

INTERNAL_KEY = 'test-internal-key'

GENERATOR_MODULES = {
    'product-translation-file': (
        'pipeline.database_updating_classes.product_updating'
        '.translation_table_generators.product_translation_table_generator'
    ),
    'brand-translation-file': (
        'pipeline.database_updating_classes.product_updating'
        '.translation_table_generators.brand_translation_table_generator'
    ),
}


@pytest.fixture(autouse=True)
def internal_api_key(monkeypatch):
    monkeypatch.setenv('INTERNAL_API_KEY', INTERNAL_KEY)


@pytest.fixture
def table_file(monkeypatch, tmp_path):
    """Point a view's generator at a file this test controls.

    The generator reads its output path from a module constant at construction
    time, so replacing the constant is enough and no stub class is needed.
    """

    def _point(url_name, contents=None):
        path = tmp_path / f'{url_name}.json'
        if contents is not None:
            path.write_text(contents, encoding='utf-8')
        monkeypatch.setattr(
            f'{GENERATOR_MODULES[url_name]}.TRANSLATION_TABLE_PATH', str(path)
        )
        return path

    return _point


@pytest.mark.django_db
@pytest.mark.parametrize('url_name', sorted(GENERATOR_MODULES))
class TestTranslationFileDownload:
    def test_the_table_on_disk_is_served(self, api_client, table_file, url_name):
        table_file(url_name, '{"old-name": "new-name"}')

        response = api_client.get(
            reverse(url_name), HTTP_X_INTERNAL_API_KEY=INTERNAL_KEY
        )

        assert response.status_code == 200, response.content
        assert response.content == b'{"old-name": "new-name"}'
        assert response['Content-Type'] == 'application/json'

    def test_an_unchanged_table_is_answered_with_a_not_modified(
        self, api_client, table_file, url_name
    ):
        """The caller re-asks on every run; the ETag is what stops it paying
        for the body twice."""
        table_file(url_name, '{"old-name": "new-name"}')

        first = api_client.get(
            reverse(url_name), HTTP_X_INTERNAL_API_KEY=INTERNAL_KEY
        )
        second = api_client.get(
            reverse(url_name),
            HTTP_X_INTERNAL_API_KEY=INTERNAL_KEY,
            HTTP_IF_NONE_MATCH=first['ETag'],
        )

        assert second.status_code == 304
        assert second.content == b''

    def test_a_changed_table_gets_a_new_tag_and_the_new_body(
        self, api_client, table_file, url_name
    ):
        path = table_file(url_name, '{"old-name": "new-name"}')
        first = api_client.get(
            reverse(url_name), HTTP_X_INTERNAL_API_KEY=INTERNAL_KEY
        )

        path.write_text('{"old-name": "newer-name"}', encoding='utf-8')
        second = api_client.get(
            reverse(url_name),
            HTTP_X_INTERNAL_API_KEY=INTERNAL_KEY,
            HTTP_IF_NONE_MATCH=first['ETag'],
        )

        assert second.status_code == 200
        assert second['ETag'] != first['ETag']
        assert second.content == b'{"old-name": "newer-name"}'

    def test_a_table_that_has_never_been_generated_is_a_404(
        self, api_client, table_file, url_name
    ):
        """Not a 500, and not an empty table: an empty translation table would
        silently normalise nothing and look like a successful run."""
        table_file(url_name)

        response = api_client.get(
            reverse(url_name), HTTP_X_INTERNAL_API_KEY=INTERNAL_KEY
        )

        assert response.status_code == 404
        assert 'update' in response.json()['error']

    def test_without_the_internal_key_the_table_is_not_served(
        self, api_client, table_file, url_name
    ):
        table_file(url_name, '{"old-name": "new-name"}')

        response = api_client.get(reverse(url_name))

        assert response.status_code in (401, 403)

    def test_the_wrong_internal_key_is_refused(
        self, api_client, table_file, url_name
    ):
        table_file(url_name, '{"old-name": "new-name"}')

        response = api_client.get(
            reverse(url_name), HTTP_X_INTERNAL_API_KEY='not-the-key'
        )

        assert response.status_code in (401, 403)


@pytest.mark.django_db
class TestTheTwoTablesAreDistinct:
    def test_each_endpoint_serves_its_own_table(self, api_client, table_file):
        """Both views are one-line subclasses differing only in
        `generator_class`, which is exactly the line a copy-paste gets wrong."""
        table_file('product-translation-file', '{"table": "products"}')
        table_file('brand-translation-file', '{"table": "brands"}')

        products = api_client.get(
            reverse('product-translation-file'),
            HTTP_X_INTERNAL_API_KEY=INTERNAL_KEY,
        )
        brands = api_client.get(
            reverse('brand-translation-file'), HTTP_X_INTERNAL_API_KEY=INTERNAL_KEY
        )

        assert products.content == b'{"table": "products"}'
        assert brands.content == b'{"table": "brands"}'
