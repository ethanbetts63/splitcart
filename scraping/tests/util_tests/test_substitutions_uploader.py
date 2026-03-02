import pytest
from unittest.mock import MagicMock, patch
from scraping.utils.command_utils.substitutions_uploader import SubstitutionsUploader


@pytest.fixture
def command():
    cmd = MagicMock()
    cmd.style.SUCCESS = lambda msg: msg
    cmd.style.ERROR = lambda msg: msg
    cmd.stdout.write = MagicMock()
    cmd.stderr.write = MagicMock()
    return cmd


class TestSubstitutionsUploaderRun:
    def test_no_file_exits_early(self, command, tmp_path):
        uploader = SubstitutionsUploader(command)
        # settings.BASE_DIR is read inside run(), so patch must cover the run() call
        with patch('scraping.utils.command_utils.substitutions_uploader.settings') as ms:
            ms.BASE_DIR = str(tmp_path)
            uploader.run()
        command.stdout.write.assert_called()

    def test_successful_upload_deletes_file(self, command, tmp_path):
        outbox = tmp_path / 'data_management' / 'data' / 'outboxes' / 'substitutions_outbox'
        outbox.mkdir(parents=True)
        subs_file = outbox / 'substitutions.json'
        subs_file.write_text('[{"product_a": "1", "product_b": "2"}]')

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None

        uploader = SubstitutionsUploader(command)
        with patch('scraping.utils.command_utils.substitutions_uploader.settings') as ms:
            ms.BASE_DIR = str(tmp_path)
            with patch('scraping.utils.command_utils.substitutions_uploader.deduplicate_substitutions',
                       return_value=[{'product_a': '1', 'product_b': '2'}]):
                with patch.object(uploader, 'get_server_url', return_value='http://test.com'):
                    with patch.object(uploader, 'get_api_key', return_value='key'):
                        with patch('scraping.utils.command_utils.substitutions_uploader.requests.post',
                                   return_value=mock_resp):
                            uploader.run()

        assert not subs_file.exists()
