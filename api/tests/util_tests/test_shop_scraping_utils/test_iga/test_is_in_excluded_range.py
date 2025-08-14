
from django.test import TestCase
from api.utils.shop_scraping_utils.iga.is_in_excluded_range import is_in_excluded_range, EXCLUDED_RANGES

class TestIsInExcludedRange(TestCase):

    def test_id_within_excluded_range(self):
        self.assertTrue(is_in_excluded_range(3000))

    def test_id_at_start_of_excluded_range(self):
        self.assertTrue(is_in_excluded_range(2115))

    def test_id_at_end_of_excluded_range(self):
        self.assertTrue(is_in_excluded_range(4350))

    def test_id_not_in_excluded_range(self):
        self.assertFalse(is_in_excluded_range(1000))

    def test_id_just_below_excluded_range(self):
        self.assertFalse(is_in_excluded_range(2114))

    def test_id_just_above_excluded_range(self):
        self.assertFalse(is_in_excluded_range(4351))

    def test_id_between_excluded_ranges(self):
        self.assertFalse(is_in_excluded_range(4356))
