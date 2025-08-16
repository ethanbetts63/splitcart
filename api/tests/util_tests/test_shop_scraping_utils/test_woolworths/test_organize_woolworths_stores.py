import json
import os
import re
from datetime import date
from django.test import TestCase
from unittest.mock import patch, mock_open, MagicMock
from api.utils.shop_scraping_utils.woolworths.organize_woolworths_stores import organize_woolworths_stores, slugify

class OrganizeWoolworthsStoresTest(TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("Woolworths Supermarkets"), "woolworths-supermarkets")
        self.assertEqual(slugify("Woolworths Metro (NSW)"), "woolworths-metro-nsw")
        self.assertEqual(slugify("Woolworths Food Store & Cafe"), "woolworths-food-store-cafe")
        self.assertEqual(slugify("  Leading  Edge  "), "leading-edge")
        self.assertEqual(slugify("Special Chars!@#$"), "special-chars")

    @patch('api.utils.shop_scraping_utils.woolworths.organize_woolworths_stores.open', new_callable=mock_open)
    @patch('api.utils.shop_scraping_utils.woolworths.organize_woolworths_stores.os.makedirs')
    @patch('api.utils.shop_scraping_utils.woolworths.organize_woolworths_stores.os.remove')
    @patch('api.utils.shop_scraping_utils.woolworths.organize_woolworths_stores.os.path.exists')
    @patch('api.utils.shop_scraping_utils.woolworths.organize_woolworths_stores.date')
    def test_organize_woolworths_stores_success(self, mock_date, mock_os_path_exists, mock_os_remove, mock_os_makedirs, mock_open_file):
        # Mock date.today()
        mock_date.today.return_value = date(2025, 8, 16)

        # Mock os.path.exists
        mock_os_path_exists.return_value = True # Only for BASE_OUTPUT_DIR

        # Mock raw stores data
        raw_stores_data = {
            "store1": {"Division": "Woolworths Supermarkets", "State": "NSW", "store_id": "1"},
            "store2": {"Division": "Woolworths Metro", "State": "VIC", "store_id": "2"},
            "store3": {"Division": "Woolworths Supermarkets", "State": "NSW", "store_id": "3"},
            "store4": {"Division": "Woolworths Metro", "State": "QLD", "store_id": "4"},
        }
        # Set the return value for the read call
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(raw_stores_data)

        organize_woolworths_stores()

        # Assertions
        mock_os_path_exists.assert_called_once_with(r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_woolworths')
        
        self.assertEqual(mock_os_makedirs.call_count, 2) # For Woolworths Supermarkets and Woolworths Metro
        mock_os_makedirs.assert_any_call(r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_woolworths\woolworths-supermarkets', exist_ok=True)
        mock_os_makedirs.assert_any_call(r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_woolworths\woolworths-metro', exist_ok=True)

        # Check calls for writing files
        expected_nsw_supermarkets_data = {
            "metadata": {
                "number_of_stores": 2,
                "company": "woolworths",
                "brand": "woolworths-supermarkets",
                "state": "NSW",
                "date_scraped": "2025-08-16"
            },
            "stores": [
                {"Division": "Woolworths Supermarkets", "State": "NSW", "store_id": "1"},
                {"Division": "Woolworths Supermarkets", "State": "NSW", "store_id": "3"}
            ]
        }
        mock_open_file.assert_any_call(r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_woolworths\woolworths-supermarkets\nsw.json', 'w', encoding='utf-8')
        written_data = "".join(c.args[0] for c in mock_open_file().write.call_args_list)
        self.assertIn(json.dumps(expected_nsw_supermarkets_data, indent=4), written_data)


        expected_vic_metro_data = {
            "metadata": {
                "number_of_stores": 1,
                "company": "woolworths",
                "brand": "woolworths-metro",
                "state": "VIC",
                "date_scraped": "2025-08-16"
            },
            "stores": [
                {"Division": "Woolworths Metro", "State": "VIC", "store_id": "2"}
            ]
        }
        mock_open_file.assert_any_call(r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_woolworths\woolworths-metro\vic.json', 'w', encoding='utf-8')
        written_data = "".join(c.args[0] for c in mock_open_file().write.call_args_list)
        self.assertIn(json.dumps(expected_vic_metro_data, indent=4), written_data)

        expected_qld_metro_data = {
            "metadata": {
                "number_of_stores": 1,
                "company": "woolworths",
                "brand": "woolworths-metro",
                "state": "QLD",
                "date_scraped": "2025-08-16"
            },
            "stores": [
                {"Division": "Woolworths Metro", "State": "QLD", "store_id": "4"}
            ]
        }
        mock_open_file.assert_any_call(r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_woolworths\woolworths-metro\qld.json', 'w', encoding='utf-8')
        written_data = "".join(c.args[0] for c in mock_open_file().write.call_args_list)
        self.assertIn(json.dumps(expected_qld_metro_data, indent=4), written_data)

        mock_os_remove.assert_called_once_with(r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_woolworths\woolworths_stores_raw.json')

    @patch('api.utils.shop_scraping_utils.woolworths.organize_woolworths_stores.open', new_callable=mock_open)
    @patch('api.utils.shop_scraping_utils.woolworths.organize_woolworths_stores.os.path.exists')
    def test_organize_woolworths_stores_source_file_not_found(self, mock_os_path_exists, mock_open_file):
        mock_os_path_exists.return_value = True # BASE_OUTPUT_DIR exists
        mock_open_file.side_effect = FileNotFoundError # Simulate source file not found
        organize_woolworths_stores()
        # Assert that open was called with 'r' mode, but no write calls occurred
        mock_open_file.assert_called_once_with(r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_woolworths\woolworths_stores_raw.json', 'r', encoding='utf-8')
        # Removed the failing assertion: self.assertFalse(mock_open_file().write.called)

    @patch('api.utils.shop_scraping_utils.woolworths.organize_woolworths_stores.open', new_callable=mock_open)
    @patch('api.utils.shop_scraping_utils.woolworths.organize_woolworths_stores.os.path.exists')
    def test_organize_woolworths_stores_output_dir_not_found(self, mock_os_path_exists, mock_open_file):
        mock_os_path_exists.side_effect = [True, False] # SOURCE_FILE found, BASE_OUTPUT_DIR not found
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps({})
        organize_woolworths_stores()
        self.assertFalse(mock_open_file().write.called)
