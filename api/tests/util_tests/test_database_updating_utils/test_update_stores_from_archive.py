import os
from django.test import TestCase
from unittest.mock import patch, MagicMock
from api.utils.database_updating_utils.update_stores_from_archive import update_stores_from_archive

class UpdateStoresFromArchiveTest(TestCase):
    @patch('api.utils.database_updating_utils.update_stores_from_archive.os.listdir')
    @patch('api.utils.database_updating_utils.update_stores_from_archive.os.path.exists')
    @patch('api.utils.database_updating_utils.update_stores_from_archive.update_stores_from_archive_file')
    def test_update_stores_from_archive_success(self, mock_update_stores_from_archive_file,
                                                 mock_os_path_exists, mock_os_listdir):
        # Mock command object
        mock_command = MagicMock()
        mock_command.stdout = MagicMock()
        mock_command.stderr = MagicMock()
        mock_command.style = MagicMock()
        mock_command.style.SQL_FIELD = MagicMock(side_effect=lambda x: x)
        mock_command.style.WARNING = MagicMock(side_effect=lambda x: x)
        mock_command.style.SUCCESS = MagicMock(side_effect=lambda x: x)
        mock_command.style.ERROR = MagicMock(side_effect=lambda x: x)

        # Mock file system
        mock_os_path_exists.return_value = True
        mock_os_listdir.return_value = ['company1.json', 'company2.json']

        # Mock update_stores_from_archive_file
        mock_update_stores_from_archive_file.side_effect = [
            ("Company A", 10),  # For company1.json
            ("Company B", 5)   # For company2.json
        ]

        # Call the function
        update_stores_from_archive(mock_command)

        # Assertions
        mock_os_path_exists.assert_called_once()
        mock_os_listdir.assert_called_once()
        self.assertEqual(mock_update_stores_from_archive_file.call_count, 2)
        mock_command.stdout.write.assert_any_call('--- Starting Store Update from Archive ---')
        mock_command.stdout.write.assert_any_call('  Successfully processed 10 stores for Company A.')
        mock_command.stdout.write.assert_any_call('  Successfully processed 5 stores for Company B.')
        mock_command.stdout.write.assert_any_call('--- Store Update from Archive Complete ---')
        mock_command.stderr.write.assert_not_called()

    @patch('api.utils.database_updating_utils.update_stores_from_archive.os.path.exists')
    def test_update_stores_from_archive_no_archive_path(self, mock_os_path_exists):
        mock_command = MagicMock()
        mock_command.stdout = MagicMock()
        mock_command.style = MagicMock()
        mock_command.style.SQL_FIELD = MagicMock(side_effect=lambda x: x)
        mock_command.style.WARNING = MagicMock(side_effect=lambda x: x)

        mock_os_path_exists.return_value = False

        update_stores_from_archive(mock_command)

        mock_command.stdout.write.assert_any_call('Company data archive directory not found.')
