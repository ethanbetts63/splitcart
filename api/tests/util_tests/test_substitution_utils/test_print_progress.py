import sys
from django.test import TestCase
from unittest.mock import patch, MagicMock
from api.utils.substitution_utils.print_progress import print_progress

class PrintProgressTest(TestCase):
    @patch('api.utils.substitution_utils.print_progress.sys.stdout.write')
    @patch('api.utils.substitution_utils.print_progress.sys.stdout.flush')
    def test_print_progress(self, mock_flush, mock_write):
        print_progress(10, 100, 5)
        expected_output = "Progress: 10 completed out of 100 (found 5 substitutes)"
        mock_write.assert_called_once_with(f"\r{expected_output}")
        mock_flush.assert_called_once()

    @patch('api.utils.substitution_utils.print_progress.sys.stdout.write')
    @patch('api.utils.substitution_utils.print_progress.sys.stdout.flush')
    def test_print_progress_completed_exceeds_total(self, mock_flush, mock_write):
        print_progress(110, 100, 15)
        expected_output = "Progress: 100 completed out of 100 (found 15 substitutes)" # Should cap at total_count
        mock_write.assert_called_once_with(f"\r{expected_output}")
        mock_flush.assert_called_once()

    @patch('api.utils.substitution_utils.print_progress.sys.stdout.write')
    @patch('api.utils.substitution_utils.print_progress.sys.stdout.flush')
    def test_print_progress_zero_values(self, mock_flush, mock_write):
        print_progress(0, 0, 0)
        expected_output = "Progress: 0 completed out of 0 (found 0 substitutes)"
        mock_write.assert_called_once_with(f"\r{expected_output}")
        mock_flush.assert_called_once()
