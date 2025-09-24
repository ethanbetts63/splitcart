import json
from django.test import TestCase
from unittest.mock import patch, mock_open
from data_management.utils.substitution_utils.load_progress import load_progress

class LoadProgressTest(TestCase):
    @patch('data_management.utils.substitution_utils.load_progress.open', new_callable=mock_open)
    def test_load_progress_file_exists(self, mock_open_file):
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps({"remaining_ids": ["id1", "id2"]})
        progress = load_progress("dummy_path.json")
        self.assertEqual(progress, {"id1", "id2"})
        mock_open_file.assert_called_once_with("dummy_path.json", 'r')

    @patch('data_management.utils.substitution_utils.load_progress.open', side_effect=FileNotFoundError)
    def test_load_progress_file_not_found(self, mock_open_file):
        progress = load_progress("dummy_path.json")
        self.assertIsNone(progress)
        mock_open_file.assert_called_once_with("dummy_path.json", 'r')

    @patch('data_management.utils.substitution_utils.load_progress.open', new_callable=mock_open)
    def test_load_progress_json_decode_error(self, mock_open_file):
        mock_open_file.return_value.__enter__.return_value.read.return_value = "invalid json"
        progress = load_progress("dummy_path.json")
        self.assertIsNone(progress)
        mock_open_file.assert_called_once_with("dummy_path.json", 'r')

    @patch('data_management.utils.substitution_utils.load_progress.open', new_callable=mock_open)
    def test_load_progress_empty_remaining_ids(self, mock_open_file):
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps({"some_other_key": "value"})
        progress = load_progress("dummy_path.json")
        self.assertEqual(progress, set())
