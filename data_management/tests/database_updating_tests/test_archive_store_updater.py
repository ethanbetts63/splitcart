from django.test import TestCase
from unittest.mock import MagicMock
import json
import os
import tempfile

from data_management.database_updating_classes.archive_store_updater import ArchiveStoreUpdater
from companies.models import Company, Division, Store

class ArchiveStoreUpdaterTests(TestCase):

    def setUp(self):
        self.mock_command = MagicMock()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    def _create_json_file(self, data):
        file_path = os.path.join(self.temp_dir, 'test_archive.json')
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return file_path

    def test_run_with_divisions(self):
        """Test processing a file with stores organized by divisions."""
        archive_data = {
            "metadata": {"company_name": "Test Company"},
            "stores_by_division": {
                "div-1": {
                    "division_name": "Test Division 1",
                    "stores_by_state": {
                        "nsw": {
                            "stores": [
                                {"store_id": "store-001", "store_name": "Sydney Store"}
                            ]
                        }
                    }
                }
            }
        }
        file_path = self._create_json_file(archive_data)
        updater = ArchiveStoreUpdater(self.mock_command, file_path)

        company_name, count = updater.run()

        self.assertEqual(company_name, "Test Company")
        self.assertEqual(count, 1)
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Division.objects.count(), 1)
        self.assertEqual(Store.objects.count(), 1)
        self.assertEqual(Store.objects.first().store_name, "Sydney Store")
        self.assertEqual(Division.objects.first().name, "Test Division 1")

    def test_run_with_states_only(self):
        """Test processing a file with stores organized only by state."""
        archive_data = {
            "metadata": {"company_name": "State Company"},
            "stores_by_state": {
                "vic": {
                    "stores": [
                        {"store_id": "store-002", "store_name": "Melbourne Store"}
                    ]
                }
            }
        }
        file_path = self._create_json_file(archive_data)
        updater = ArchiveStoreUpdater(self.mock_command, file_path)

        company_name, count = updater.run()

        self.assertEqual(company_name, "State Company")
        self.assertEqual(count, 1)
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Division.objects.count(), 0)
        self.assertEqual(Store.objects.count(), 1)
        self.assertEqual(Store.objects.first().store_name, "Melbourne Store")
