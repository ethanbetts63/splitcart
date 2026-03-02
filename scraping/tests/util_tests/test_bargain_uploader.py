import pytest
import json
from unittest.mock import MagicMock, patch
from scraping.utils.command_utils.bargain_uploader import BargainUploader


@pytest.fixture
def command():
    cmd = MagicMock()
    cmd.style.SUCCESS = lambda msg: msg
    cmd.style.WARNING = lambda msg: msg
    cmd.style.ERROR = lambda msg: msg
    cmd.stdout.write = MagicMock()
    cmd.stderr.write = MagicMock()
    return cmd


@pytest.fixture
def uploader(command, tmp_path):
    with patch('scraping.utils.command_utils.bargain_uploader.settings') as mock_settings:
        mock_settings.BASE_DIR = str(tmp_path)
        u = BargainUploader(command)
    u.source_dir = str(tmp_path / 'bargains')
    return u


class TestBargainUploaderRun:
    def test_no_directory_exits_early(self, uploader, command):
        # source_dir doesn't exist
        uploader.run()
        command.stdout.write.assert_called()
        # No HTTP calls

    def test_no_json_files_exits_early(self, uploader, tmp_path, command):
        (tmp_path / 'bargains').mkdir()
        uploader.run()
        # Stdout called with warning, no HTTP

    def test_successful_upload_deletes_files(self, uploader, tmp_path, command):
        bargain_dir = tmp_path / 'bargains'
        bargain_dir.mkdir()
        test_file = bargain_dir / 'bargains_2024.json'
        test_file.write_text('{"test": "data"}', encoding='utf-8')

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None

        with patch.object(uploader, 'get_server_url', return_value='http://test.com'):
            with patch.object(uploader, 'get_api_key', return_value='test-key'):
                with patch('scraping.utils.command_utils.bargain_uploader.requests.post', return_value=mock_response):
                    uploader.run()

        assert not test_file.exists()

    def test_upload_failure_raises_exception(self, uploader, tmp_path, command):
        import requests
        bargain_dir = tmp_path / 'bargains'
        bargain_dir.mkdir()
        (bargain_dir / 'test.json').write_text('{}')

        with patch.object(uploader, 'get_server_url', return_value='http://test.com'):
            with patch.object(uploader, 'get_api_key', return_value='key'):
                with patch('scraping.utils.command_utils.bargain_uploader.requests.post',
                           side_effect=requests.exceptions.RequestException('fail')):
                    with pytest.raises(requests.exceptions.RequestException):
                        uploader.run()
