
from django.test import TestCase
from api.utils.shop_scraping_utils.aldi.drange import drange

class DRangeTest(TestCase):

    def test_positive_integer_step(self):
        """Test drange with positive integer steps."""
        self.assertEqual(list(drange(1, 5, 1)), [1, 2, 3, 4, 5])
        self.assertEqual(list(drange(1, 6, 2)), [1, 3, 5])

    def test_floating_point_step(self):
        """Test drange with floating-point steps."""
        self.assertEqual(list(drange(1.0, 2.0, 0.5)), [1.0, 1.5, 2.0])
        self.assertEqual(list(drange(0.1, 0.3, 0.1)), [0.1, 0.2, 0.3])

    def test_start_and_stop_same(self):
        """Test drange when start and stop are the same."""
        self.assertEqual(list(drange(5, 5, 1)), [5])
        self.assertEqual(list(drange(5.0, 5.0, 0.1)), [5.0])

    def test_step_larger_than_range(self):
        """Test drange when the step is larger than the range."""
        self.assertEqual(list(drange(1, 3, 5)), [1])
        self.assertEqual(list(drange(1.0, 1.5, 1.0)), [1.0])

    def test_stop_less_than_start(self):
        """Test drange when stop is less than start (should yield nothing)."""
        self.assertEqual(list(drange(5, 1, 1)), [])
        self.assertEqual(list(drange(5.0, 1.0, 0.5)), [])

    def test_zero_step(self):
        """Test drange with a zero step (should yield start indefinitely, so limit iterations)."""
        result = []
        for i, val in enumerate(drange(1, 10, 0)):
            if i >= 5: # Limit to 5 iterations
                break
            result.append(val)
        self.assertEqual(result, [1, 1, 1, 1, 1])

        result_float = []
        for i, val in enumerate(drange(2.5, 5.0, 0)):
            if i >= 3: # Limit to 3 iterations
                break
            result_float.append(val)
        self.assertEqual(result_float, [2.5, 2.5, 2.5])
