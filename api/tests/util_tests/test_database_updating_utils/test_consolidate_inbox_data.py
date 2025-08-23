import os
import json
import tempfile
import shutil
from django.test import TestCase
from unittest.mock import Mock
from api.utils.database_updating_utils.consolidate_inbox_data import consolidate_inbox_data

class TestConsolidateInboxData(TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.inbox_path = os.path.join(self.temp_dir, 'product_inbox')
        os.makedirs(self.inbox_path, exist_ok=True)

        self.mock_command = Mock()
        self.mock_command.stdout = Mock()
        self.mock_command.stderr = Mock()
        self.mock_command.style = Mock()

        # Create dummy inbox files
        self.file1_path = os.path.join(self.inbox_path, "file1.jsonl")
        with open(self.file1_path, 'w') as f:
            data1 = {"product": {"normalized_name_brand_size": "key1", "price_current": 1.00}, "metadata": {"company": "TestCo"}}
            data2 = {"product": {"normalized_name_brand_size": "key2", "price_current": 2.00}, "metadata": {"company": "TestCo"}}
            f.write(json.dumps(data1) + '\n')
            f.write(json.dumps(data2) + '\n')

        self.file2_path = os.path.join(self.inbox_path, "file2.jsonl")
        with open(self.file2_path, 'w') as f:
            data3 = {"product": {"normalized_name_brand_size": "key2", "price_current": 2.50}, "metadata": {"company": "TestCo"}} # Duplicate key
            data4 = {"product": {"normalized_name_brand_size": "key3", "price_current": 3.00}, "metadata": {"company": "TestCo"}}
            f.write(json.dumps(data3) + '\n')
            f.write(json.dumps(data4) + '\n')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_consolidate_inbox_data_success(self):
        consolidated_data, processed_files = consolidate_inbox_data(self.inbox_path, self.mock_command)

        self.assertEqual(len(consolidated_data), 3)
        self.assertIn("key1", consolidated_data)
        self.assertIn("key2", consolidated_data)
        self.assertIn("key3", consolidated_data)

        # Test "last one wins" for duplicate key
        self.assertEqual(consolidated_data['key2']['product_details']['price_current'], 2.50)

        self.assertEqual(len(processed_files), 2)
        self.assertIn(self.file1_path, processed_files)
        self.assertIn(self.file2_path, processed_files)