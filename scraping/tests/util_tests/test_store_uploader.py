import pytest
from unittest.mock import MagicMock, patch
from scraping.utils.command_utils.store_uploader import StoreUploader


@pytest.fixture
def command():
    cmd = MagicMock()
    cmd.style.SUCCESS = lambda msg: msg
    cmd.style.ERROR = lambda msg: msg
    cmd.stdout.write = MagicMock()
    cmd.stderr.write = MagicMock()
    return cmd


class TestStoreUploaderRun:
    def test_no_files_exits_early(self, command, tmp_path):
        uploader = StoreUploader(command)
        # settings.BASE_DIR is read inside run(), so patch must cover the run() call
        with patch('scraping.utils.command_utils.store_uploader.settings') as ms:
            ms.BASE_DIR = str(tmp_path)
            with patch.object(uploader, 'get_server_url', return_value='http://test.com'):
                with patch.object(uploader, 'get_api_key', return_value='key'):
                    uploader.run()
        command.stdout.write.assert_called()

    def test_successful_upload_archives_file(self, command, tmp_path):
        outbox = tmp_path / 'scraping' / 'data' / 'outboxes' / 'store_outbox'
        outbox.mkdir(parents=True)
        archive = tmp_path / 'scraping' / 'data' / 'temp_json_store_storage'
        archive.mkdir(parents=True)
        store_file = outbox / 'woolworths_1001.json'
        store_file.write_text('{"store_data": {}}')

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None

        uploader = StoreUploader(command)
        with patch('scraping.utils.command_utils.store_uploader.settings') as ms:
            ms.BASE_DIR = str(tmp_path)
            with patch.object(uploader, 'get_server_url', return_value='http://test.com'):
                with patch.object(uploader, 'get_api_key', return_value='key'):
                    with patch('scraping.utils.command_utils.store_uploader.requests.post', return_value=mock_resp):
                        uploader.run()

        assert not store_file.exists()
        assert (archive / 'woolworths_1001.json').exists()
