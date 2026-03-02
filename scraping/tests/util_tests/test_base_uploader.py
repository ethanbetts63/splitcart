import pytest
from unittest.mock import MagicMock, patch
from scraping.utils.command_utils.base_uploader import BaseUploader


@pytest.fixture
def command():
    cmd = MagicMock()
    cmd.style.ERROR = lambda msg: msg
    cmd.style.SUCCESS = lambda msg: msg
    cmd.stderr.write = MagicMock()
    cmd.stdout.write = MagicMock()
    return cmd


@pytest.fixture
def uploader(command):
    return BaseUploader(command, dev=False)


class TestGetServerUrl:
    def test_dev_mode_returns_localhost(self, command):
        uploader = BaseUploader(command, dev=True)
        assert uploader.get_server_url() == 'http://127.0.0.1:8000'

    def test_prod_mode_returns_api_server_url(self, uploader):
        with patch('scraping.utils.command_utils.base_uploader.settings') as mock_settings:
            mock_settings.API_SERVER_URL = 'https://api.example.com'
            result = uploader.get_server_url()
        assert result == 'https://api.example.com'

    def test_prod_mode_empty_url_returns_none(self, uploader, command):
        with patch('scraping.utils.command_utils.base_uploader.settings') as mock_settings:
            mock_settings.API_SERVER_URL = ''
            result = uploader.get_server_url()
        assert result is None
        command.stderr.write.assert_called()

    def test_prod_mode_missing_attribute_returns_none(self, uploader, command):
        with patch('scraping.utils.command_utils.base_uploader.settings') as mock_settings:
            del mock_settings.API_SERVER_URL
            type(mock_settings).__getattr__ = MagicMock(side_effect=AttributeError)
            result = uploader.get_server_url()
        assert result is None


class TestGetApiKey:
    def test_returns_api_key_from_settings(self, uploader):
        with patch('scraping.utils.command_utils.base_uploader.settings') as mock_settings:
            mock_settings.INTERNAL_API_KEY = 'secret-key-123'
            result = uploader.get_api_key()
        assert result == 'secret-key-123'

    def test_empty_key_returns_none(self, uploader, command):
        with patch('scraping.utils.command_utils.base_uploader.settings') as mock_settings:
            mock_settings.INTERNAL_API_KEY = ''
            result = uploader.get_api_key()
        assert result is None
        command.stderr.write.assert_called()

    def test_missing_attribute_returns_none(self, uploader, command):
        with patch('scraping.utils.command_utils.base_uploader.settings') as mock_settings:
            type(mock_settings).__getattr__ = MagicMock(side_effect=AttributeError)
            result = uploader.get_api_key()
        assert result is None
