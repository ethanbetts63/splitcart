
import os
import json
import unittest
from unittest.mock import Mock
import tempfile
import shutil

from api.utils.database_updating_utils.consolidate_inbox_data import consolidate_inbox_data

class TestConsolidateInboxData(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test_consolidate_data(self):
        # Create dummy files
        product_1 = {
            "product": {
                "normalized_name_brand_size": "key1",
                "price_current": 10.0,
                "is_on_sale": False,
                "store_product_id": "spid1",
                "category_path": ["cat1", "cat2"]
            },
            "metadata": {
                "store_id": "store1",
                "company": "companyA"
            }
        }
        product_2 = {
            "product": {
                "normalized_name_brand_size": "key2",
                "price_current": 20.0,
                "is_on_sale": True,
                "store_product_id": "spid2",
                "category_path": ["cat3"]
            },
            "metadata": {
                "store_id": "store2",
                "company": "companyB"
            }
        }
        # This product will overwrite product_1 because of the same key
        product_3 = {
            "product": {
                "normalized_name_brand_size": "key1",
                "price_current": 12.0,
                "is_on_sale": True,
                "store_product_id": "spid3",
                "category_path": ["cat4"]
            },
            "metadata": {
                "store_id": "store3",
                "company": "companyC"
            }
        }

        # Write a .json file
        with open(os.path.join(self.test_dir, "file1.json"), 'w') as f:
            json.dump(product_1, f)

        # Write a .jsonl file
        with open(os.path.join(self.test_dir, "file2.jsonl"), 'w') as f:
            f.write(json.dumps(product_2) + '\n')
            f.write(json.dumps(product_3) + '\n')

        # Create a mock command object
        mock_command = Mock()
        mock_command.stdout = Mock()
        mock_command.stderr = Mock()
        mock_command.style.ERROR = lambda x: x


        # Run the function
        consolidated_data, processed_files = consolidate_inbox_data(self.test_dir, mock_command)

        # Assertions
        self.assertEqual(len(processed_files), 2)
        self.assertEqual(len(consolidated_data), 2)

        # Check product_2 data (from key2)
        self.assertIn("key2", consolidated_data)
        self.assertEqual(consolidated_data["key2"]["product_details"]["price_current"], 20.0)

        # Check product_3 data (from key1, overwriting product_1)
        self.assertIn("key1", consolidated_data)
        self.assertEqual(consolidated_data["key1"]["product_details"]["price_current"], 12.0)
        self.assertTrue(consolidated_data["key1"]["price_history"][0]["is_on_special"])
        self.assertEqual(consolidated_data["key1"]["company_name"], "companyC")

if __name__ == '__main__':
    unittest.main()
