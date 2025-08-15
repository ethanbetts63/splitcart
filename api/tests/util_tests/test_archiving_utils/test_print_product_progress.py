
import sys
import io
from django.test import TestCase
from api.utils.archiving_utils.print_product_progress import print_product_progress

class PrintProductProgressTest(TestCase):
    def test_print_product_progress(self):
        # Redirect stdout to a string buffer
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        print_product_progress(10)

        # Restore stdout
        sys.stdout = old_stdout

        # Check the output
        self.assertEqual(captured_output.getvalue(), '\r  Processing product 10...')