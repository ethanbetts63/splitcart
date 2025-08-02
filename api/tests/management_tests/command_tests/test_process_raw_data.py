from django.core.management import call_command
from django.test import TestCase
from unittest.mock import patch, call
import os
from django.conf import settings

class ProcessRawDataCommandTest(TestCase):

    @patch('api.management.commands.process_raw_data.file_finder')
    @patch('api.management.commands.process_raw_data.data_combiner')
    @patch('api.management.commands.process_raw_data.archive_manager')
    def test_handle_command_all_stores(self, mock_archive_manager, mock_data_combiner, mock_file_finder):
        mock_scrape_plan = {
            'coles': {
                '2025-08-01T120000': {
                    'meat-seafood': ['coles_meat_1.json', 'coles_meat_2.json'],
                    'fruit-vegetables': ['coles_fruit_1.json']
                }
            },
            'woolworths': {
                '2025-08-01T130000': {
                    'fruit-veg': ['woolies_fruit_1.json']
                }
            }
        }
        mock_file_finder.return_value = mock_scrape_plan
        mock_data_combiner.return_value = [{'product': 'test'}]

        call_command('process_raw_data')

        api_app_path = os.path.join(settings.BASE_DIR, 'api')
        raw_data_path = os.path.join(api_app_path, 'data', 'raw_data')
        processed_data_path = os.path.join(api_app_path, 'data', 'processed_data')

        mock_file_finder.assert_called_once_with(raw_data_path)
        
        combiner_calls = [
            call(['coles_meat_1.json', 'coles_meat_2.json']),
            call(['coles_fruit_1.json']),
            call(['woolies_fruit_1.json'])
        ]
        mock_data_combiner.assert_has_calls(combiner_calls, any_order=True)

        archive_calls = [
            call(processed_data_path, 'coles', '2025-08-01', 'meat-seafood', [{'product': 'test'}], ['coles_meat_1.json', 'coles_meat_2.json']),
            call(processed_data_path, 'coles', '2025-08-01', 'fruit-vegetables', [{'product': 'test'}], ['coles_fruit_1.json']),
            call(processed_data_path, 'woolworths', '2025-08-01', 'fruit-veg', [{'product': 'test'}], ['woolies_fruit_1.json'])
        ]
        mock_archive_manager.assert_has_calls(archive_calls, any_order=True)

    @patch('api.management.commands.process_raw_data.file_finder')
    @patch('api.management.commands.process_raw_data.data_combiner')
    @patch('api.management.commands.process_raw_data.archive_manager')
    def test_handle_command_specific_store(self, mock_archive_manager, mock_data_combiner, mock_file_finder):
        mock_scrape_plan = {
            'coles': {
                '2025-08-01T120000': {
                    'meat-seafood': ['coles_meat_1.json', 'coles_meat_2.json'],
                }
            },
            'woolworths': {
                '2025-08-01T130000': {
                    'fruit-veg': ['woolies_fruit_1.json']
                }
            }
        }
        mock_file_finder.return_value = mock_scrape_plan
        mock_data_combiner.return_value = [{'product': 'test'}]

        call_command('process_raw_data', 'coles')

        processed_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'processed_data')

        mock_data_combiner.assert_called_once_with(['coles_meat_1.json', 'coles_meat_2.json'])
        mock_archive_manager.assert_called_once_with(
            processed_data_path, 'coles', '2025-08-01', 'meat-seafood', [{'product': 'test'}], ['coles_meat_1.json', 'coles_meat_2.json']
        )

    @patch('api.management.commands.process_raw_data.file_finder')
    @patch('api.management.commands.process_raw_data.data_combiner')
    @patch('api.management.commands.process_raw_data.archive_manager')
    def test_handle_command_no_files(self, mock_archive_manager, mock_data_combiner, mock_file_finder):
        mock_file_finder.return_value = {}
        call_command('process_raw_data')
        mock_data_combiner.assert_not_called()
        mock_archive_manager.assert_not_called()

    @patch('api.management.commands.process_raw_data.file_finder')
    @patch('api.management.commands.process_raw_data.data_combiner')
    @patch('api.management.commands.process_raw_data.archive_manager')
    def test_handle_command_invalid_store(self, mock_archive_manager, mock_data_combiner, mock_file_finder):
        mock_scrape_plan = {
            'coles': {
                '2025-08-01T120000': {
                    'meat-seafood': ['coles_meat_1.json'],
                }
            }
        }
        mock_file_finder.return_value = mock_scrape_plan
        call_command('process_raw_data', 'invalid_store')
        mock_data_combiner.assert_not_called()
        mock_archive_manager.assert_not_called()
