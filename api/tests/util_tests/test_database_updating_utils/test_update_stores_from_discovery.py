import os
import json
from django.test import TestCase
from unittest.mock import patch, MagicMock, mock_open
from django.conf import settings # Import settings
from api.utils.database_updating_utils.update_stores_from_discovery import update_stores_from_discovery, process_store_file

class UpdateStoresFromDiscoveryTest(TestCase):
    @patch('api.utils.database_updating_utils.update_stores_from_discovery.os.listdir')
    @patch('api.utils.database_updating_utils.update_stores_from_discovery.os.path.exists')
    @patch('api.utils.database_updating_utils.update_stores_from_discovery.open', new_callable=mock_open)
    @patch('api.utils.database_updating_utils.update_stores_from_discovery.os.remove')
    @patch('api.utils.database_updating_utils.update_stores_from_discovery.get_or_create_company')
    @patch('api.utils.database_updating_utils.update_stores_from_discovery.get_or_create_division')
    @patch('api.utils.database_updating_utils.update_stores_from_discovery.get_or_create_store')
    @patch('api.utils.database_updating_utils.update_stores_from_discovery.time.sleep')
    def test_update_stores_from_discovery_success(self, mock_time_sleep, mock_get_or_create_store,
                                                   mock_get_or_create_division, mock_get_or_create_company,
                                                   mock_os_remove, mock_open_file, mock_os_path_exists,
                                                   mock_os_listdir):
        # Mock command object
        mock_command = MagicMock()
        mock_command.stdout = MagicMock()
        mock_command.stderr = MagicMock()
        mock_command.style = MagicMock()
        mock_command.style.SQL_FIELD = MagicMock(side_effect=lambda x: x)
        mock_command.style.WARNING = MagicMock(side_effect=lambda x: x)
        mock_command.style.SUCCESS = MagicMock(side_effect=lambda x: x)

        # Mock file system
        mock_os_path_exists.return_value = True
        mock_os_listdir.side_effect = [['store1.json'], [], []] # First call returns a file, then empty, then empty again

        # Sample JSON data
        sample_data = {
            "metadata": {"company": "Coles"},
            "store_data": {
                "store_id": "123",
                "brand": {"name": "Coles Supermarkets", "id": "coles-supermarkets", "storeFinderId": "coles-supermarkets"}
            }
        }
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(sample_data)

        # Mock database interactions
        mock_company = MagicMock()
        mock_division = MagicMock()
        mock_store = MagicMock()
        mock_get_or_create_company.return_value = (mock_company, True)
        mock_get_or_create_division.return_value = (mock_division, True)
        mock_get_or_create_store.return_value = (mock_store, True)

        # Call the function
        update_stores_from_discovery(mock_command)

        # Assertions
        mock_os_path_exists.assert_called_once()
        self.assertEqual(mock_os_listdir.call_count, 3) # Called three times due to the loop
        mock_open_file.assert_called_once()
        mock_os_remove.assert_called_once()
        mock_get_or_create_company.assert_called_once_with("Coles")
        mock_get_or_create_division.assert_called_once_with(company_obj=mock_company, division_name="Coles Supermarkets", external_id="coles-supermarkets", store_finder_id="coles-supermarkets")
        mock_get_or_create_store.assert_called_once_with(company_obj=mock_company, division_obj=mock_division, store_id="123", store_data=sample_data['store_data'])
        mock_time_sleep.assert_called_once_with(500)
        mock_command.stdout.write.assert_any_call('Found 1 file(s) to process...')
        mock_command.stdout.write.assert_any_call('No new store files found. Waiting 500 seconds...')
        mock_command.stdout.write.assert_any_call('No new files found after waiting. Exiting.')

    @patch('api.utils.database_updating_utils.update_stores_from_discovery.os.path.exists')
    def test_update_stores_from_discovery_no_directory(self, mock_os_path_exists):
        mock_command = MagicMock()
        mock_command.stdout = MagicMock()
        mock_command.style = MagicMock()
        mock_command.style.WARNING = MagicMock(side_effect=lambda x: x)

        mock_os_path_exists.return_value = False

        update_stores_from_discovery(mock_command)

        mock_command.stdout.write.assert_any_call(mock_command.style.WARNING(f"'{os.path.join(settings.BASE_DIR, 'api', 'data', 'discovered_stores')}' not found. Nothing to process."))