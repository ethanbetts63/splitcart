import pytest
import os
from unittest.mock import MagicMock, patch
import requests
from scraping.utils.python_file_downloader import fetch_python_file


@pytest.fixture
def dest_path(tmp_path):
    return str(tmp_path / 'output' / 'test_file.py')


class TestFetchPythonFile:
    def _patch_settings(self):
        return patch('scraping.utils.python_file_downloader.settings',
                     API_SERVER_URL='http://test-server.com',
                     INTERNAL_API_KEY='test-key-123')

    def test_saves_file_on_200_response(self, dest_path):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = 'translations = {}'
        mock_resp.headers.get.return_value = None
        mock_resp.raise_for_status.return_value = None

        with self._patch_settings():
            with patch('scraping.utils.python_file_downloader.requests.get', return_value=mock_resp):
                fetch_python_file('product_translations', dest_path)

        assert os.path.exists(dest_path)
        with open(dest_path) as f:
            assert f.read() == 'translations = {}'

    def test_saves_etag_when_present(self, dest_path):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = 'data = {}'
        mock_resp.headers.get.return_value = '"etag-abc123"'
        mock_resp.raise_for_status.return_value = None

        with self._patch_settings():
            with patch('scraping.utils.python_file_downloader.requests.get', return_value=mock_resp):
                fetch_python_file('product_translations', dest_path)

        etag_path = dest_path + '.etag'
        assert os.path.exists(etag_path)
        with open(etag_path) as f:
            assert f.read() == '"etag-abc123"'

    def test_skips_write_on_304(self, dest_path):
        mock_resp = MagicMock()
        mock_resp.status_code = 304

        with self._patch_settings():
            with patch('scraping.utils.python_file_downloader.requests.get', return_value=mock_resp):
                fetch_python_file('product_translations', dest_path)

        assert not os.path.exists(dest_path)

    def test_sends_etag_header_if_cached(self, dest_path, tmp_path):
        etag_path = dest_path + '.etag'
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(etag_path, 'w') as f:
            f.write('"cached-etag"')

        mock_resp = MagicMock()
        mock_resp.status_code = 304

        with self._patch_settings():
            with patch('scraping.utils.python_file_downloader.requests.get', return_value=mock_resp) as mock_get:
                fetch_python_file('product_translations', dest_path)
                call_headers = mock_get.call_args[1]['headers']
                assert call_headers.get('If-None-Match') == '"cached-etag"'

    def test_returns_early_when_no_api_key(self, dest_path):
        with patch('scraping.utils.python_file_downloader.settings',
                   API_SERVER_URL='http://test.com', INTERNAL_API_KEY=None):
            fetch_python_file('product_translations', dest_path)
        assert not os.path.exists(dest_path)

    def test_handles_request_exception_gracefully(self, dest_path):
        with self._patch_settings():
            with patch('scraping.utils.python_file_downloader.requests.get',
                       side_effect=requests.exceptions.RequestException('error')):
                # Should not raise
                fetch_python_file('product_translations', dest_path, command=MagicMock())
        assert not os.path.exists(dest_path)
