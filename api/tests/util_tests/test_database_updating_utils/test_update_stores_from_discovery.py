
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from api.utils.database_updating_utils.update_stores_from_discovery import update_stores_from_discovery

class UpdateStoresFromDiscoveryTest(TestCase):
    def setUp(self):
        self.mock_command = MagicMock()

    @patch('api.utils.database_updating_utils.update_stores_from_discovery.process_store_file')
    @patch('time.sleep')
    @patch('os.listdir')
    @patch('os.path.exists', return_value=True)
    def test_files_found_and_processed(self, mock_exists, mock_listdir, mock_sleep, mock_process):
        mock_listdir.side_effect = [["store1.json"], [], []]

        update_stores_from_discovery(self.mock_command)

        mock_process.assert_called_once()
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('api.utils.database_updating_utils.update_stores_from_discovery.process_store_file')
    @patch('time.sleep')
    @patch('os.listdir')
    @patch('os.path.exists', return_value=True)
    def test_no_files_initially(self, mock_exists, mock_listdir, mock_sleep, mock_process):
        mock_listdir.side_effect = [[], []] # First call is empty, second is also empty to exit

        update_stores_from_discovery(self.mock_command)

        mock_process.assert_not_called()
        mock_sleep.assert_called_once_with(30)
