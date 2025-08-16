import os
from django.test import TestCase
from django.core.management import call_command
from unittest.mock import patch, MagicMock

class GetWoolworthsSubstitutesCommandTest(TestCase):
    @patch('api.management.commands.get_woolworths_substitutes.requests.Session')
    @patch('api.management.commands.get_woolworths_substitutes.get_woolworths_product_store_ids')
    @patch('api.management.commands.get_woolworths_substitutes.load_progress')
    @patch('api.management.commands.get_woolworths_substitutes.save_progress')
    @patch('api.management.commands.get_woolworths_substitutes.fetch_substitutes_from_api')
    @patch('api.management.commands.get_woolworths_substitutes.get_product_by_store_id')
    @patch('api.management.commands.get_woolworths_substitutes.link_products_as_substitutes')
    @patch('api.management.commands.get_woolworths_substitutes.save_discovered_product')
    @patch('api.management.commands.get_woolworths_substitutes.os.path.exists')
    @patch('api.management.commands.get_woolworths_substitutes.os.remove')
    def test_command_runs_successfully(self, mock_os_remove, mock_os_path_exists, mock_save_discovered_product,
                                       mock_link_products_as_substitutes, mock_get_product_by_store_id,
                                       mock_fetch_substitutes_from_api, mock_save_progress, mock_load_progress,
                                       mock_get_woolworths_product_store_ids, mock_session):

        # Mock setup_session
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.get.return_value.status_code = 200 # For session warmup
        
        # Mock load_progress to indicate no existing progress
        mock_load_progress.return_value = None

        # Mock get_woolworths_product_store_ids
        mock_get_woolworths_product_store_ids.return_value = {'prod1', 'prod2'}

        # Mock fetch_substitutes_from_api
        mock_fetch_substitutes_from_api.side_effect = [
            [{'Stockcode': 'sub1'}], # For prod1
            [{'Stockcode': 'sub2'}]  # For prod2
        ]

        # Mock get_product_by_store_id
        mock_original_product = MagicMock(id=1)
        mock_substitute_product = MagicMock(id=2)
        mock_get_product_by_store_id.side_effect = [
            mock_original_product, # For prod1
            mock_substitute_product, # For sub1
            mock_original_product, # For prod2
            mock_substitute_product # For sub2
        ]

        # Mock os.path.exists for progress file
        mock_os_path_exists.return_value = True

        # Call the management command
        call_command('get_woolworths_substitutes')

        # Assertions
        mock_session.assert_called_once()
        mock_session_instance.get.assert_called_once() # For session warmup
        mock_load_progress.assert_called_once()
        mock_get_woolworths_product_store_ids.assert_called_once()
        self.assertEqual(mock_fetch_substitutes_from_api.call_count, 2) # Called for prod1 and prod2
        self.assertEqual(mock_get_product_by_store_id.call_count, 4) # Called for prod1, sub1, prod2, sub2
        self.assertEqual(mock_link_products_as_substitutes.call_count, 2) # Called for sub1 and sub2
        mock_save_progress.assert_called() # Called multiple times
        mock_os_remove.assert_called_once() # Progress file should be removed at the end
