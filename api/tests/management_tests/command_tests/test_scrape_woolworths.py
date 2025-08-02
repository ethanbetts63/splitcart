from django.core.management import call_command
from django.test import TestCase
from unittest.mock import patch
import os
from django.conf import settings

class ScrapeWoolworthsCommandTest(TestCase):

    @patch('api.management.commands.scrape_woolworths.scrape_and_save_woolworths_data')
    def test_handle_command(self, mock_scrape_and_save):
        call_command('scrape_woolworths')

        expected_categories = [
            ('fruit-veg', '1-E5BEE36E'),
            ('poultry-meat-seafood', '1_D5A2236'),
            ('meal-occasions', '1_8AD6702'),
            ('deli', '1_3151F6F'),
            ('dairy-eggs-fridge', '1_6E4F4E4'),
            ('bakery', '1_DEB537E'),
            ('lunch-box', '1_9E92C35'),
            ('freezer', '1_ACA2FC2'),
            ('snacks-confectionery', '1_717445A'),
            ('pantry', '1_39FD49C'),
            ('international-foods', '1_F229FBE'),
            ('drinks', '1_5AF3A0A'),
            ('beer-wine-spirits', '1_8E4DA6F'),
            ('beauty', '1_8D61DD6'),
            ('personal-care', '1_894D0A8'),
            ('health-wellness', '1_9851658'),
            ('cleaning-maintenance', '1_2432B58'),
            ('baby', '1_717A94B'),
            ('pet', '1_61D6FEB'),
            ('electronics', '1_B863F57'),
            ('home-lifestyle', '1_DEA3ED5'),
        ]
        
        raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')

        mock_scrape_and_save.assert_called_once_with(expected_categories, raw_data_path)
