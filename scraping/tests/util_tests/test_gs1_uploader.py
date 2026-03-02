import pytest
from unittest.mock import MagicMock, patch
from scraping.utils.command_utils.gs1_uploader import Gs1Uploader


@pytest.fixture
def command():
    cmd = MagicMock()
    cmd.style.SUCCESS = lambda msg: msg
    cmd.style.ERROR = lambda msg: msg
    cmd.stdout.write = MagicMock()
    cmd.stderr.write = MagicMock()
    return cmd


class TestGs1UploaderRun:
    def test_no_files_exits_early(self, command, tmp_path):
        uploader = Gs1Uploader(command)
        # settings.BASE_DIR is read inside run(), so patch must cover the run() call
        with patch('scraping.utils.command_utils.gs1_uploader.settings') as ms:
            ms.BASE_DIR = str(tmp_path)
            with patch.object(uploader, 'get_server_url', return_value='http://test.com'):
                with patch.object(uploader, 'get_api_key', return_value='key'):
                    uploader.run()
        command.stdout.write.assert_called()

    def test_successful_upload_archives_file(self, command, tmp_path):
        outbox = tmp_path / 'data_management' / 'data' / 'outboxes' / 'gs1_outbox'
        outbox.mkdir(parents=True)
        archive = tmp_path / 'data_management' / 'data' / 'inboxes' / 'gs1_storage'
        archive.mkdir(parents=True)
        gs1_file = outbox / 'gs1_results.jsonl'
        gs1_file.write_text('{"license_key": "123"}')

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None

        uploader = Gs1Uploader(command)
        with patch('scraping.utils.command_utils.gs1_uploader.settings') as ms:
            ms.BASE_DIR = str(tmp_path)
            with patch.object(uploader, 'get_server_url', return_value='http://test.com'):
                with patch.object(uploader, 'get_api_key', return_value='key'):
                    with patch('scraping.utils.command_utils.gs1_uploader.requests.post', return_value=mock_resp):
                        uploader.run()

        assert not gs1_file.exists()
        assert (archive / 'gs1_results.jsonl').exists()
