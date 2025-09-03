
import os
import shutil
import tempfile
from django.test import TestCase
from unittest.mock import MagicMock, patch

from api.database_updating_classes.archive_update_orchestrator import ArchiveUpdateOrchestrator

class ArchiveUpdateOrchestratorTests(TestCase):

    def setUp(self):
        self.mock_command = MagicMock()
        self.orchestrator = ArchiveUpdateOrchestrator(self.mock_command)
        self.temp_dir = tempfile.mkdtemp()
        # Override the default paths to use a temporary directory
        self.orchestrator.company_archive_path = self.temp_dir
        self.orchestrator.store_archive_path = self.temp_dir

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('api.database_updating_classes.archive_update_orchestrator.ProductUpdater')
    @patch('api.database_updating_classes.archive_update_orchestrator.StoreUpdater')
    def test_run_with_no_flags(self, mock_store_updater, mock_product_updater):
        """Test that run() does nothing if no flags are provided."""
        self.orchestrator.run()
        mock_store_updater.assert_not_called()
        mock_product_updater.assert_not_called()

    @patch('api.database_updating_classes.archive_update_orchestrator.ProductUpdater')
    @patch('api.database_updating_classes.archive_update_orchestrator.StoreUpdater')
    def test_run_with_update_products_flag(self, mock_store_updater, mock_product_updater):
        """Test that only the ProductUpdater is called when update_products is True."""
        self.orchestrator.run(update_products=True)
        mock_store_updater.assert_not_called()
        mock_product_updater.assert_called_once_with(self.mock_command, self.temp_dir)
        mock_product_updater.return_value.run.assert_called_once()

    @patch('api.database_updating_classes.archive_update_orchestrator.ProductUpdater')
    @patch('api.database_updating_classes.archive_update_orchestrator.StoreUpdater')
    def test_run_with_update_stores_flag(self, mock_store_updater, mock_product_updater):
        """Test that only the StoreUpdater is called when update_stores is True."""
        # Configure the mock to return the expected tuple
        mock_store_updater.return_value.run.return_value = ('Test Company', 1)

        # Create a dummy file for the orchestrator to find
        dummy_file_path = os.path.join(self.temp_dir, 'company.json')
        with open(dummy_file_path, 'w') as f:
            f.write('{}')

        self.orchestrator.run(update_stores=True)
        mock_product_updater.assert_not_called()
        mock_store_updater.assert_called_once_with(self.mock_command, dummy_file_path)
        mock_store_updater.return_value.run.assert_called_once()

    @patch('api.database_updating_classes.archive_update_orchestrator.ProductUpdater')
    @patch('api.database_updating_classes.archive_update_orchestrator.StoreUpdater')
    def test_run_with_both_flags(self, mock_store_updater, mock_product_updater):
        """Test that both updaters are called when both flags are True."""
        # Configure the mock to return the expected tuple
        mock_store_updater.return_value.run.return_value = ('Test Company', 1)

        dummy_file_path = os.path.join(self.temp_dir, 'company.json')
        with open(dummy_file_path, 'w') as f:
            f.write('{}')

        self.orchestrator.run(update_stores=True, update_products=True)
        
        mock_store_updater.assert_called_once_with(self.mock_command, dummy_file_path)
        mock_store_updater.return_value.run.assert_called_once()
        
        mock_product_updater.assert_called_once_with(self.mock_command, self.temp_dir)
        mock_product_updater.return_value.run.assert_called_once()
