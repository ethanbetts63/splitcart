
from django.test import TestCase
from unittest.mock import MagicMock
from api.utils.database_updating_utils.tally_counter import TallyCounter

class TallyCounterTest(TestCase):
    def test_tally_counter(self):
        tally = TallyCounter()

        # Test initial state
        self.assertEqual(tally.created, 0)
        self.assertEqual(tally.updated, 0)
        self.assertEqual(tally.created_per_company, {})

        # Test incrementing created
        tally.increment(True, "Company A")
        self.assertEqual(tally.created, 1)
        self.assertEqual(tally.updated, 0)
        self.assertEqual(tally.created_per_company, {"Company A": 1})

        # Test incrementing updated
        tally.increment(False)
        self.assertEqual(tally.created, 1)
        self.assertEqual(tally.updated, 1)

        # Test incrementing created for another company
        tally.increment(True, "Company B")
        self.assertEqual(tally.created, 2)
        self.assertEqual(tally.created_per_company, {"Company A": 1, "Company B": 1})

        # Test incrementing created for an existing company
        tally.increment(True, "Company A")
        self.assertEqual(tally.created, 3)
        self.assertEqual(tally.created_per_company, {"Company A": 2, "Company B": 1})

    def test_display(self):
        tally = TallyCounter()
        tally.increment(True, "Company A")
        tally.increment(True, "Company A")
        tally.increment(True, "Company B")
        tally.increment(False)

        mock_command = MagicMock()
        mock_command.stdout.write = MagicMock()

        tally.display(mock_command)

        expected_msg = "--- Tally: 3 Created (Company A: 2, Company B: 1), 1 Updated ---"
        mock_command.stdout.write.assert_called_once_with(expected_msg)
