import pytest
from unittest.mock import MagicMock, patch
from scraping.utils.command_utils.category_links_uploader import CategoryLinksUploader


@pytest.fixture
def command():
    cmd = MagicMock()
    cmd.style.SUCCESS = lambda msg: msg
    cmd.style.ERROR = lambda msg: msg
    cmd.stdout.write = MagicMock()
    cmd.stderr.write = MagicMock()
    return cmd


class TestCategoryLinksUploaderRun:
    def test_no_file_exits_early(self, command, tmp_path):
        uploader = CategoryLinksUploader(command)
        # settings.BASE_DIR is read inside run(), so patch must cover the run() call
        with patch('scraping.utils.command_utils.category_links_uploader.settings') as ms:
            ms.BASE_DIR = str(tmp_path)
            uploader.run()
        command.stdout.write.assert_called()

    def test_successful_upload_deletes_file(self, command, tmp_path):
        outbox = tmp_path / 'data_management' / 'data' / 'outboxes' / 'category_links_outbox'
        outbox.mkdir(parents=True)
        cat_file = outbox / 'category_links.json'
        cat_file.write_text('[{"slug": "dairy"}]')

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None

        uploader = CategoryLinksUploader(command)
        with patch('scraping.utils.command_utils.category_links_uploader.settings') as ms:
            ms.BASE_DIR = str(tmp_path)
            with patch.object(uploader, 'get_server_url', return_value='http://test.com'):
                with patch.object(uploader, 'get_api_key', return_value='key'):
                    with patch('scraping.utils.command_utils.category_links_uploader.requests.post', return_value=mock_resp):
                        uploader.run()

        assert not cat_file.exists()
