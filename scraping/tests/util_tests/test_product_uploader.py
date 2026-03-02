import pytest
import json
from unittest.mock import MagicMock, patch
from scraping.utils.command_utils.product_uploader import ProductUploader


@pytest.fixture
def command():
    cmd = MagicMock()
    cmd.style.SUCCESS = lambda msg: msg
    cmd.style.ERROR = lambda msg: msg
    cmd.stdout.write = MagicMock()
    cmd.stderr.write = MagicMock()
    return cmd


def _make_jsonl_line(store_id, date_str):
    return json.dumps({'metadata': {'store_id': store_id, 'scraped_date': date_str}}) + '\n'


class TestProductUploaderLatestFileScan:
    """Tests that the scanner correctly identifies the latest file per store."""

    def test_no_files_exits_early(self, command, tmp_path):
        # ProductUploader.run() reads settings.BASE_DIR, so the patch must wrap run()
        uploader = ProductUploader(command)
        with patch('scraping.utils.command_utils.product_uploader.settings') as ms:
            ms.BASE_DIR = str(tmp_path)
            with patch.object(uploader, 'get_server_url', return_value='http://test.com'):
                with patch.object(uploader, 'get_api_key', return_value='key'):
                    uploader.run()
        command.stdout.write.assert_any_call('No files to process.')

    def test_latest_file_selected_per_store(self, command, tmp_path):
        """Only the most recent file per store should be uploaded; older ones archived."""
        # run() uses: settings.BASE_DIR / 'data_management' / 'data' / 'outboxes' / 'product_outbox'
        outbox = tmp_path / 'data_management' / 'data' / 'outboxes' / 'product_outbox'
        outbox.mkdir(parents=True)
        archive = tmp_path / 'data_management' / 'data' / 'inboxes' / 'temp_jsonl_product_storage'
        archive.mkdir(parents=True)

        # Two files for same store — newer should be uploaded
        old_file = outbox / 'store1-2024-01-01.jsonl'
        new_file = outbox / 'store1-2024-06-01.jsonl'
        old_file.write_text(_make_jsonl_line('STORE1', '2024-01-01'))
        new_file.write_text(_make_jsonl_line('STORE1', '2024-06-01'))

        uploaded_files = []

        def mock_post(url, headers, files, timeout):
            uploaded_files.append(files['file'][0])
            resp = MagicMock()
            resp.raise_for_status.return_value = None
            return resp

        uploader = ProductUploader(command)
        with patch('scraping.utils.command_utils.product_uploader.settings') as ms:
            ms.BASE_DIR = str(tmp_path)
            with patch.object(uploader, 'get_server_url', return_value='http://test.com'):
                with patch.object(uploader, 'get_api_key', return_value='key'):
                    with patch('scraping.utils.command_utils.product_uploader.requests.post', side_effect=mock_post):
                        with patch('scraping.utils.command_utils.product_uploader.run_sanity_checks', return_value=[]):
                            uploader.run()

        # Only one file should have been uploaded (the newer one's .gz)
        assert len(uploaded_files) == 1
        assert '2024-06-01' in uploaded_files[0]
