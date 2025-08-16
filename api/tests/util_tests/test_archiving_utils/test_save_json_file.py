import json
from django.test import TestCase
from unittest.mock import patch, mock_open, call
from api.utils.archiving_utils.save_json_file import save_json_file

class SaveJsonFileTest(TestCase):
    @patch('api.utils.archiving_utils.save_json_file.os.makedirs')
    @patch('api.utils.archiving_utils.save_json_file.open', new_callable=mock_open)
    def test_save_json_file(self, mock_open_file, mock_makedirs):
        company_slug = 'test-company'
        store_id = '123'
        data_dict = {'key': 'value'}

        file_path = save_json_file(company_slug, store_id, data_dict)

        mock_makedirs.assert_called_once()
        mock_open_file.assert_called_once_with(file_path, 'w', encoding='utf-8')
        
        # Get the file handle from the mock
        handle = mock_open_file()
        
        # Check that json.dump was called with the correct data
        written_data = "".join(c[0][0] for c in handle.write.call_args_list)
        self.assertEqual(written_data, json.dumps(data_dict, indent=4))