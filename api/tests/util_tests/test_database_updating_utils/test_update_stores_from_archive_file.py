import json
from django.test import TestCase
from unittest.mock import patch, mock_open, MagicMock
from api.utils.database_updating_utils.update_stores_from_archive_file import update_stores_from_archive_file

class UpdateStoresFromArchiveFileTest(TestCase):
    @patch('api.utils.database_updating_utils.update_stores_from_archive_file.open', new_callable=mock_open)
    @patch('api.utils.database_updating_utils.update_stores_from_archive_file.get_or_create_company')
    @patch('api.utils.database_updating_utils.update_stores_from_archive_file.get_or_create_division')
    @patch('api.utils.database_updating_utils.update_stores_from_archive_file.get_or_create_store')
    def test_update_stores_from_archive_file_with_divisions(self, mock_get_or_create_store,
                                                            mock_get_or_create_division,
                                                            mock_get_or_create_company,
                                                            mock_open_file):
        # Sample JSON data with divisions
        sample_data = {
            "metadata": {"company_name": "TestCompany"},
            "stores_by_division": {
                "division-a": {
                    "division_name": "Division A",
                    "stores_by_state": {
                        "state-1": {
                            "stores": [
                                {"store_id": "store1", "name": "Store 1"},
                                {"store_id": "store2", "name": "Store 2"}
                            ]
                        }
                    }
                },
                "division-b": {
                    "division_name": "Division B",
                    "stores_by_state": {
                        "state-2": {
                            "stores": [
                                {"store_id": "store3", "name": "Store 3"}
                            ]
                        }
                    }
                }
            }
        }
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(sample_data)

        mock_company_obj = MagicMock()
        mock_get_or_create_company.return_value = (mock_company_obj, True)
        mock_division_obj_a = MagicMock()
        mock_division_obj_b = MagicMock()
        mock_get_or_create_division.side_effect = [(mock_division_obj_a, True), (mock_division_obj_b, True)]
        mock_get_or_create_store.return_value = (MagicMock(), True)

        company_name, total_stores = update_stores_from_archive_file("dummy_path.json")

        self.assertEqual(company_name, "TestCompany")
        self.assertEqual(total_stores, 3)
        mock_get_or_create_company.assert_called_once_with("TestCompany")
        self.assertEqual(mock_get_or_create_division.call_count, 2)
        self.assertEqual(mock_get_or_create_store.call_count, 3)

    @patch('api.utils.database_updating_utils.update_stores_from_archive_file.open', new_callable=mock_open)
    @patch('api.utils.database_updating_utils.update_stores_from_archive_file.get_or_create_company')
    @patch('api.utils.database_updating_utils.update_stores_from_archive_file.get_or_create_division')
    @patch('api.utils.database_updating_utils.update_stores_from_archive_file.get_or_create_store')
    def test_update_stores_from_archive_file_without_divisions(self, mock_get_or_create_store,
                                                                mock_get_or_create_division,
                                                                mock_get_or_create_company,
                                                                mock_open_file):
        # Sample JSON data without divisions
        sample_data = {
            "metadata": {"company_name": "AnotherCompany"},
            "stores_by_state": {
                "state-a": {
                    "stores": [
                        {"store_id": "storeX", "name": "Store X"},
                        {"store_id": "storeY", "name": "Store Y"}
                    ]
                }
            }
        }
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(sample_data)

        mock_company_obj = MagicMock()
        mock_get_or_create_company.return_value = (mock_company_obj, True)
        mock_get_or_create_store.return_value = (MagicMock(), True)

        company_name, total_stores = update_stores_from_archive_file("dummy_path.json")

        self.assertEqual(company_name, "AnotherCompany")
        self.assertEqual(total_stores, 2)
        mock_get_or_create_company.assert_called_once_with("AnotherCompany")
        mock_get_or_create_division.assert_not_called()
        self.assertEqual(mock_get_or_create_store.call_count, 2)

    @patch('api.utils.database_updating_utils.update_stores_from_archive_file.open', new_callable=mock_open)
    def test_update_stores_from_archive_file_json_decode_error(self, mock_open_file):
        mock_open_file.return_value.__enter__.return_value.read.return_value = "invalid json"
        company_name, total_stores = update_stores_from_archive_file("dummy_path.json")
        self.assertIsNone(company_name)
        self.assertEqual(total_stores, 0)

    @patch('api.utils.database_updating_utils.update_stores_from_archive_file.open', side_effect=FileNotFoundError)
    def test_update_stores_from_archive_file_not_found(self, mock_open_file):
        company_name, total_stores = update_stores_from_archive_file("dummy_path.json")
        self.assertIsNone(company_name)
        self.assertEqual(total_stores, 0)

    @patch('api.utils.database_updating_utils.update_stores_from_archive_file.open', new_callable=mock_open)
    def test_update_stores_from_archive_file_missing_company_name(self, mock_open_file):
        sample_data = {"metadata": {}, "stores_by_state": {}}
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(sample_data)
        company_name, total_stores = update_stores_from_archive_file("dummy_path.json")
        self.assertIsNone(company_name)
        self.assertEqual(total_stores, 0)
