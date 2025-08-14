
import sys
from io import StringIO
from django.test import TestCase
from unittest.mock import patch
from api.utils.shop_scraping_utils.woolworths.print_progress_bar import print_progress_bar

class TestPrintProgressBar(TestCase):

    def setUp(self):
        self.held_stdout = sys.stdout
        sys.stdout = StringIO()

    def tearDown(self):
        sys.stdout = self.held_stdout

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_progress_bar_start(self, mock_stdout):
        """Test the progress bar at the beginning of the process."""
        print_progress_bar(0, 100, -33.86, 151.20, 0)
        output = mock_stdout.getvalue()
        self.assertIn("Progress: |----------------------------------------| 0.00% (0/100)", output)
        self.assertIn("Stores Found: 0", output)
        self.assertIn("Coords: (-33.86, 151.20)", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_progress_bar_mid(self, mock_stdout):
        """Test the progress bar in the middle of the process."""
        print_progress_bar(50, 100, -34.00, 151.00, 25)
        output = mock_stdout.getvalue()
        self.assertIn("|████████████████████--------------------| 50.00% (50/100)", output)
        self.assertIn("Stores Found: 25", output)
        self.assertIn("Coords: (-34.00, 151.00)", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_progress_bar_end(self, mock_stdout):
        """Test the progress bar at the end of the process."""
        print_progress_bar(100, 100, -35.00, 150.00, 50)
        output = mock_stdout.getvalue()
        self.assertIn("|████████████████████████████████████████| 100.00% (100/100)", output)
        self.assertIn("Stores Found: 50", output)
        self.assertIn("Coords: (-35.00, 150.00)", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_coordinates_formatting(self, mock_stdout):
        """Test that coordinates are formatted to two decimal places."""
        print_progress_bar(1, 100, -33.12345, 151.67890, 5)
        output = mock_stdout.getvalue()
        self.assertIn("Coords: (-33.12, 151.68)", output)
