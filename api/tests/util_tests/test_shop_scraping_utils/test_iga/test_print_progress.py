
import sys
from io import StringIO
from django.test import TestCase
from unittest.mock import patch
from api.utils.shop_scraping_utils.iga.print_progress import print_progress

class TestPrintProgress(TestCase):

    def setUp(self):
        self.held_stdout = sys.stdout
        sys.stdout = StringIO()

    def tearDown(self):
        sys.stdout = self.held_stdout

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_progress_start(self, mock_stdout):
        """Test the progress bar at the beginning of the process."""
        print_progress(0, 100, 0, "Starting...")
        output = mock_stdout.getvalue()
        self.assertIn("Progress: |------------------------------| 0.00%", output)
        self.assertIn("Found: 0", output)
        self.assertIn("Starting...", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_progress_mid(self, mock_stdout):
        """Test the progress bar in the middle of the process."""
        print_progress(50, 100, 25, "Processing...")
        output = mock_stdout.getvalue()
        self.assertIn("|███████████████---------------| 50.00%", output)
        self.assertIn("Found: 25", output)
        self.assertIn("Processing...", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_progress_end(self, mock_stdout):
        """Test the progress bar at the end of the process."""
        print_progress(100, 100, 50, "Finished.")
        output = mock_stdout.getvalue()
        self.assertIn("|██████████████████████████████| 100.00%", output)
        self.assertIn("Found: 50", output)
        self.assertIn("Finished.", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_no_message(self, mock_stdout):
        """Test the progress bar with no message."""
        print_progress(10, 100, 5)
        output = mock_stdout.getvalue()
        self.assertIn("|███---------------------------| 10.00%", output)
        self.assertIn("Found: 5", output)
