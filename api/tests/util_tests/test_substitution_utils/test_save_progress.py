import json
from django.test import TestCase
from unittest.mock import patch, mock_open
from api.utils.substitution_utils.save_progress import save_progress

class SaveProgressTest(TestCase):
    @patch('api.utils.substitution_utils.save_progress.open', new_callable=mock_open)
    def test_save_progress(self, mock_open_file):
        file_path = "dummy_path.json"
        remaining_ids = {"id1", "id2", "id3"}

        save_progress(file_path, remaining_ids)

        mock_open_file.assert_called_once_with(file_path, 'w')
        
        # Check the written content
        written_data_str = "".join(c.args[0] for c in mock_open_file().write.call_args_list)
        written_data_dict = json.loads(written_data_str)
        
        # Sort the list from the written data for consistent comparison
        written_data_dict['remaining_ids'].sort()

        expected_data = {"remaining_ids": sorted(list(remaining_ids))}
        self.assertEqual(written_data_dict, expected_data)