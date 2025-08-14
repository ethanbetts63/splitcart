
from django.test import TestCase
from api.utils.shop_scraping_utils.woolworths.drange import drange

class TestDRange(TestCase):

    def test_positive_step(self):
        self.assertEqual(list(drange(1, 5, 1)), [1, 2, 3, 4, 5])
        self.assertEqual(list(drange(1, 5, 2)), [1, 3, 5])

    def test_negative_step(self):
        # drange is not designed for negative steps, this confirms its behavior
        self.assertEqual(list(drange(5, 1, -1)), [])

    def test_step_larger_than_range(self):
        self.assertEqual(list(drange(1, 5, 10)), [1])

    def test_zero_step(self):
        # This would be an infinite loop, so we test a few iterations
        result = []
        for i, val in enumerate(drange(1, 5, 0)):
            if i >= 5:
                break
            result.append(val)
        self.assertEqual(result, [1, 1, 1, 1, 1])

    def test_float_numbers(self):
        self.assertEqual(list(drange(1.0, 2.0, 0.5)), [1.0, 1.5, 2.0])
