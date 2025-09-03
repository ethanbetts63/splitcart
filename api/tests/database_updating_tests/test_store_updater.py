
import os
import json
import shutil
import tempfile
from django.test import TestCase
from unittest.mock import MagicMock

from api.database_updating_classes.store_updater import StoreUpdater
from companies.models import Company, Division, Store
from companies.tests.test_helpers.model_factories import StoreFactory

class StoreUpdaterTests(TestCase):

    def setUp(self):
        self.mock_command = MagicMock()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

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
        updater = StoreUpdater(self.mock_command, file_path)

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
        updater = StoreUpdater(self.mock_command, file_path)

        company_name, count = updater.run()

        self.assertEqual(company_name, "State Company")
        self.assertEqual(count, 1)
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Division.objects.count(), 0)
        self.assertEqual(Store.objects.count(), 1)
        self.assertEqual(Store.objects.first().store_name, "Melbourne Store")

    def test_run_updates_existing_store(self):
        """Test that an existing store is updated with new information."""
        # Create an initial store
        existing_store = StoreFactory(store_id='store-003', store_name='Old Name', phone_number='111')
        
        archive_data = {
            "metadata": {"company_name": existing_store.company.name},
            "stores_by_state": {
                "qld": {
                    "stores": [
                        {"store_id": "store-003", "store_name": "New Name", "phone_number": "999"}
                    ]
                }
            }
        }
        file_path = self._create_json_file(archive_data)
        updater = StoreUpdater(self.mock_command, file_path)

        initial_store_count = Store.objects.count()
        updater.run()

        self.assertEqual(Store.objects.count(), initial_store_count) # No new store created
        existing_store.refresh_from_db()
        self.assertEqual(existing_store.store_name, "New Name")
        self.assertEqual(existing_store.phone_number, "999")

    def test_run_with_invalid_json_file(self):
        """Test that the updater handles a non-existent or invalid file gracefully."""
        file_path = os.path.join(self.temp_dir, 'non_existent.json')
        updater = StoreUpdater(self.mock_command, file_path)
        
        company_name, count = updater.run()

        self.assertIsNone(company_name)
        self.assertEqual(count, 0)
        self.assertEqual(Company.objects.count(), 0)
