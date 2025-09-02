import unittest
from unittest.mock import MagicMock, patch, mock_open
import requests
import io

from api.scrapers.barcode_scraper_coles import ColesBarcodeScraper

class TestColesBarcodeScraper(unittest.TestCase):

    @patch('api.scrapers.barcode_scraper_coles.prefill_barcodes_from_db', return_value=[])
    @patch('api.scrapers.barcode_scraper_coles.JsonlWriter')
    @patch('builtins.open', new_callable=mock_open, read_data='{"metadata": {"store_id": "123", "store_name": "Test Store", "state": "TS"}}\n')
    def test_run_stops_after_3_consecutive_network_errors(self, mock_file, mock_jsonl_writer, mock_prefill):
        """
        Test that the run loop breaks after 3 consecutive network errors.
        """
        # Arrange
        mock_command = MagicMock()
        mock_stdout = io.StringIO()
        mock_stderr = io.StringIO()
        mock_command.stdout.write = mock_stdout.write
        mock_command.stderr.write = mock_stderr.write
        mock_command.style.ERROR = lambda x: x # Make the style wrapper transparent

        scraper = ColesBarcodeScraper(command=mock_command, source_file_path='fake/path.jsonl')

        # Mock methods to isolate the run loop
        scraper.setup = MagicMock()
        scraper.get_work_items = MagicMock(return_value=[{'product': {'url': 'http://fake.url'}}] * 5)
        scraper.fetch_data_for_item = MagicMock(side_effect=requests.exceptions.RequestException("Test network error"))
        scraper.write_data = MagicMock()
        scraper.jsonl_writer = MagicMock()
        scraper.output = MagicMock()

        # Act
        scraper.run()

        # Assert
        # 1. Check that fetch_data_for_item was called exactly 3 times
        self.assertEqual(scraper.fetch_data_for_item.call_count, 3, "fetch_data_for_item should be called 3 times before stopping.")

        # 2. Check the stdout/stderr logs for the correct messages
        stdout_output = mock_stdout.getvalue()
        stderr_output = mock_stderr.getvalue()
        self.assertIn("Consecutive network failures: 1", stdout_output)
        self.assertIn("Consecutive network failures: 2", stdout_output)
        self.assertIn("Consecutive network failures: 3", stdout_output)
        self.assertIn("Stopping scraper due to 3 consecutive network failures.", stderr_output)

        # 3. Check that the loop terminated and didn't try a 4th time
        self.assertNotIn("Consecutive network failures: 4", stdout_output)

        # 4. Check that the final success message is not present
        self.assertNotIn("Barcode enrichment complete.", stdout_output)


if __name__ == '__main__':
    unittest.main()
