from django.test import TestCase
from unittest.mock import Mock
from api.utils.database_updating_utils.tally_counter import TallyCounter

class TallyCounterTest(TestCase):

    def setUp(self):
        self.counter = TallyCounter()

    def test_initialization(self):
        """Test that counters are initialized to zero."""
        self.assertEqual(self.counter.created, 0)
        self.assertEqual(self.counter.updated, 0)
        self.assertEqual(self.counter.created_per_company, {})

    def test_increment_created(self):
        """Test incrementing the created counter."""
        self.counter.increment(created=True)
        self.assertEqual(self.counter.created, 1)
        self.assertEqual(self.counter.updated, 0)

    def test_increment_updated(self):
        """Test incrementing the updated counter."""
        self.counter.increment(created=False)
        self.assertEqual(self.counter.created, 0)
        self.assertEqual(self.counter.updated, 1)

    def test_increment_created_with_company(self):
        """Test incrementing created counter with a company name."""
        self.counter.increment(created=True, company_name="Coles")
        self.assertEqual(self.counter.created, 1)
        self.assertEqual(self.counter.created_per_company, {"Coles": 1})

        self.counter.increment(created=True, company_name="Coles")
        self.assertEqual(self.counter.created, 2)
        self.assertEqual(self.counter.created_per_company, {"Coles": 2})

        self.counter.increment(created=True, company_name="Woolworths")
        self.assertEqual(self.counter.created, 3)
        self.assertEqual(self.counter.created_per_company, {"Coles": 2, "Woolworths": 1})

    def test_reset(self):
        """Test resetting all counters."""
        self.counter.increment(created=True)
        self.counter.increment(created=False)
        self.counter.increment(created=True, company_name="Coles")
        self.counter.reset()
        self.assertEqual(self.counter.created, 0)
        self.assertEqual(self.counter.updated, 0)
        self.assertEqual(self.counter.created_per_company, {})

    def test_get_total(self):
        """Test getting the total number of items processed."""
        self.counter.increment(created=True)
        self.counter.increment(created=False)
        self.assertEqual(self.counter.get_total(), 2)

    def test_get_created(self):
        """Test getting the total number of items created."""
        self.counter.increment(created=True)
        self.counter.increment(created=True)
        self.counter.increment(created=False)
        self.assertEqual(self.counter.get_created(), 2)

    def test_get_updated(self):
        """Test getting the total number of items updated."""
        self.counter.increment(created=True)
        self.counter.increment(created=False)
        self.counter.increment(created=False)
        self.assertEqual(self.counter.get_updated(), 2)

    def test_get_created_per_company(self):
        """Test getting the dictionary of created items per company."""
        self.counter.increment(created=True, company_name="Coles")
        self.counter.increment(created=True, company_name="Woolworths")
        self.counter.increment(created=True, company_name="Coles")
        self.assertEqual(self.counter.get_created_per_company(), {"Coles": 2, "Woolworths": 1})

    def test_display(self):
        """Test displaying the tally."""
        mock_command = Mock()
        self.counter.increment(created=True, company_name="Coles")
        self.counter.increment(created=False)
        self.counter.display(mock_command)
        expected_msg = "--- Tally: 1 Created (Coles: 1), 1 Updated ---"
        mock_command.stdout.write.assert_called_with(expected_msg)

    def test_str_representation(self):
        """Test the string representation."""
        self.counter.increment(created=True)
        self.counter.increment(created=False)
        self.assertEqual(str(self.counter), "Created: 1, Updated: 1")

    def test_repr_representation(self):
        """Test the representation."""
        self.counter.increment(created=True)
        self.counter.increment(created=False)
        self.assertEqual(repr(self.counter), "TallyCounter(created=1, updated=1)")
