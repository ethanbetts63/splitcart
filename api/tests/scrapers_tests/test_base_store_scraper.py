import unittest
from unittest.mock import MagicMock, patch
import requests
import io

from api.scrapers.base_store_scraper import BaseStoreScraper

# A minimal concrete implementation of the abstract BaseStoreScraper for testing purposes
class ConcreteStoreScraper(BaseStoreScraper):
    def __init__(self, command):
        super().__init__(command, 'test_company', 'test_progress')

    def setup(self):
        pass

    def get_work_items(self) -> list:
        # Provide a dummy list of items to iterate over
        return [1, 2, 3, 4, 5]

    def fetch_data_for_item(self, item) -> list:
        # This will be mocked in the tests
        return []

    def clean_raw_data(self, raw_data: dict) -> dict:
        return {}

    def get_item_type(self) -> str:
        return "TestItem"

class TestBaseStoreScraper(unittest.TestCase):

    def setUp(self):
        # Mock the command object that the scraper expects
        self.mock_command = MagicMock()
        # Use io.StringIO to capture stdout writes
        self.mock_stdout = io.StringIO()
        self.mock_command.stdout.write = self.mock_stdout.write
        
        # Instantiate our concrete scraper for testing
        self.scraper = ConcreteStoreScraper(self.mock_command)

    @patch('os.path.exists', return_value=False)
    @patch('builtins.open')
    @patch('os.remove')
    def test_run_stops_after_3_consecutive_network_errors(self, mock_remove, mock_open, mock_exists):
        """
        Test that the scraper's run loop breaks after 3 consecutive network errors.
        """
        # Arrange: Mock fetch_data_for_item to simulate a network error
        self.scraper.fetch_data_for_item = MagicMock(side_effect=requests.exceptions.RequestException("Test network error"))

        # Act: Run the scraper
        self.scraper.run()

        # Assert
        # 1. Check that fetch_data_for_item was called exactly 3 times
        self.assertEqual(self.scraper.fetch_data_for_item.call_count, 3, "fetch_data_for_item should be called 3 times before stopping.")

        # 2. Check the stdout log to ensure the correct messages were printed
        output = self.mock_stdout.getvalue()
        self.assertIn("Consecutive network failures: 1", output)
        self.assertIn("Consecutive network failures: 2", output)
        self.assertIn("Consecutive network failures: 3", output)
        self.assertIn("Stopping scraper due to 3 consecutive network failures.", output)

        # 3. Check that the loop terminated and didn't try a 4th time
        self.assertNotIn("Consecutive network failures: 4", output)

    @patch('os.path.exists')
    @patch('builtins.open')
    @patch('os.remove')
    def test_run_completes_successfully(self, mock_remove, mock_open, mock_exists):
        """
        Test the successful execution path of the scraper.
        """
        # Arrange
        # 1st call in load_progress(), 2nd in cleanup()
        mock_exists.side_effect = [False, True]

        self.scraper.fetch_data_for_item = MagicMock(return_value=[{'data': 'some_data'}])
        self.scraper.clean_raw_data = MagicMock(return_value={'store_data': {'store_id': '123'}})
        self.scraper.save_store = MagicMock()
        
        # Act
        self.scraper.run()

        # Assert
        # 1. Check that fetch_data_for_item was called for all items
        self.assertEqual(self.scraper.fetch_data_for_item.call_count, 5, "fetch_data_for_item should be called for all 5 work items.")

        # 2. Check that clean_raw_data and save_store were also called
        self.assertEqual(self.scraper.clean_raw_data.call_count, 5)
        self.assertEqual(self.scraper.save_store.call_count, 5)

        # 3. Check that the progress file was removed on completion
        mock_remove.assert_called_with(self.scraper.progress_file)

        # 4. Check for the final success message
        output = self.mock_stdout.getvalue()
        self.assertIn(f"Finished {self.scraper.company} store scraping.", output)

if __name__ == '__main__':
    unittest.main()
