import pytest
import json
from requests.exceptions import RequestException
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


def _make_jsonl_line(company_name, date_str):
    return json.dumps({'metadata': {'company_name': company_name, 'scraped_date': date_str}}) + '\n'


class TestProductUploaderLatestFileScan:
    """Tests that the scanner correctly identifies the latest file per company."""

    def test_no_files_exits_early(self, command, tmp_path):
        # ProductUploader.run() reads settings.BASE_DIR, so the patch must wrap run()
        uploader = ProductUploader(command)
        with patch('scraping.utils.command_utils.product_uploader.settings') as ms:
            ms.BASE_DIR = str(tmp_path)
            ms.PIPELINE_DATA_DIR = tmp_path / 'pipeline' / 'data'
            with patch.object(uploader, 'get_server_url', return_value='http://test.com'):
                with patch.object(uploader, 'get_api_key', return_value='key'):
                    uploader.run()
        command.stdout.write.assert_any_call('No files to process.')

    def test_latest_file_selected_per_company(self, command, tmp_path):
        """Only the most recent file per store should be uploaded; older ones archived."""
        # run() uses: settings.BASE_DIR / 'pipeline' / 'data' / 'outboxes' / 'product_outbox'
        outbox = tmp_path / 'pipeline' / 'data' / 'outboxes' / 'product_outbox'
        outbox.mkdir(parents=True)
        archive = tmp_path / 'pipeline' / 'data' / 'archive' / 'product_archive'
        archive.mkdir(parents=True)

        # Two files for same store — newer should be uploaded
        old_file = outbox / 'coles-2024-01-01.jsonl'
        new_file = outbox / 'coles-2024-06-01.jsonl'
        old_file.write_text(_make_jsonl_line('Coles', '2024-01-01'))
        new_file.write_text(_make_jsonl_line('Coles', '2024-06-01'))

        uploaded_files = []

        def mock_post(url, headers, files, timeout):
            uploaded_files.append(files['file'][0])
            resp = MagicMock()
            resp.raise_for_status.return_value = None
            return resp

        uploader = ProductUploader(command)
        with patch('scraping.utils.command_utils.product_uploader.settings') as ms:
            ms.BASE_DIR = str(tmp_path)
            ms.PIPELINE_DATA_DIR = tmp_path / 'pipeline' / 'data'
            with patch.object(uploader, 'get_server_url', return_value='http://test.com'):
                with patch.object(uploader, 'get_api_key', return_value='key'):
                    with patch('scraping.utils.command_utils.product_uploader.requests.post', side_effect=mock_post):
                        with patch('scraping.utils.command_utils.product_uploader.run_sanity_checks', return_value=[]):
                            uploader.run()

        # Only one file should have been uploaded (the newer one's .gz)
        assert len(uploaded_files) == 1
        assert '2024-06-01' in uploaded_files[0]
        assert (archive / old_file.name).exists()
        assert (archive / new_file.name).exists()

    def test_failed_latest_upload_stays_in_outbox(self, command, tmp_path):
        outbox = tmp_path / 'pipeline' / 'data' / 'outboxes' / 'product_outbox'
        outbox.mkdir(parents=True)
        archive = tmp_path / 'pipeline' / 'data' / 'archive' / 'product_archive'
        archive.mkdir(parents=True)
        product_file = outbox / 'coles-2024-06-01.jsonl'
        product_file.write_text(_make_jsonl_line('Coles', '2024-06-01'))

        uploader = ProductUploader(command)
        with patch('scraping.utils.command_utils.product_uploader.settings') as ms:
            ms.BASE_DIR = str(tmp_path)
            ms.PIPELINE_DATA_DIR = tmp_path / 'pipeline' / 'data'
            with patch.object(uploader, 'get_server_url', return_value='http://test.com'):
                with patch.object(uploader, 'get_api_key', return_value='key'):
                    with patch('scraping.utils.command_utils.product_uploader.requests.post', side_effect=RequestException):
                        with patch('scraping.utils.command_utils.product_uploader.run_sanity_checks', return_value=[]):
                            uploader.run()

        assert product_file.exists()
        assert not (archive / product_file.name).exists()
