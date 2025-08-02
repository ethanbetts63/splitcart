from django.core.management import call_command
from django.test import TestCase
from unittest.mock import patch
import os
from django.conf import settings

class ScrapeColesCommandTest(TestCase):

    @patch('api.management.commands.scrape_coles.scrape_and_save_coles_data')
    def test_handle_command(self, mock_scrape_and_save):
        call_command('scrape_coles')

        expected_categories = [
            "meat-seafood",
            "fruit-vegetables",
            "dairy-eggs-fridge",
            "bakery",
            "deli",
            "pantry",
            "dietary-world-foods",
            "chips-chocolates-snacks"
            "drinks",
            "frozen",
            "household",
            "health-beauty",
            "baby",
            "pet",
            "liquorland",
        ]
        
        raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')

        mock_scrape_and_save.assert_called_once_with(expected_categories, raw_data_path)
