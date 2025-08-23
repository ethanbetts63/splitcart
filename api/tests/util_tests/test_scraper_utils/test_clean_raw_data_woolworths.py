
import unittest
from unittest.mock import patch
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_woolworths import clean_raw_data_woolworths

class TestCleanRawDataWoolworths(unittest.TestCase):

    @patch('api.utils.scraper_utils.clean_raw_data_woolworths.normalize_product_data', side_effect=lambda p: p)
    def test_clean_raw_data_woolworths(self, mock_normalize):
        raw_product_list = [
            {
                "Stockcode": 136341,
                "Barcode": "0265178000003",
                "Name": "Woolworths Bird's Eye Chilli Hot",
                "Brand": "Woolworths",
                "Description": "Woolworths Bird's Eye Chilli<br>Hot each",
                "PackageSize": "each",
                "Price": 0.14,
                "WasPrice": 0.14,
                "IsOnSpecial": False,
                "SavingsAmount": 0.0,
                "CupPrice": 0.14,
                "CupMeasure": "1EA",
                "CupString": "$0.14 / 1EA",
                "IsAvailable": True,
                "IsInStock": True,
                "SupplyLimit": 36,
                "LargeImageFile": "https://cdn1.woolworths.media/content/wowproductimages/large/136341.jpg",
                "UrlFriendlyName": "woolworths-bird-s-eye-chilli-hot",
                "AdditionalAttributes": {
                    "countryoforigin": "Australia",
                    "healthstarrating": "5",
                    "ingredients": "Chilli",
                    "allergenmaybepresent": "May contain traces of nuts",
                    "sapdepartmentname": "FRUIT AND VEG",
                    "sapcategoryname": "VEG / FRESHCUTS / HARD PRODUCE",
                    "sapsubcategoryname": "CHILLIES",
                    "sapsegmentname": "CHILLIES LOOSE"
                },
                "Rating": {
                    "Average": 4.5,
                    "ReviewCount": 10
                },
                "CentreTag": {"TagType": "PROMOTION"},
                "ImageTag": {"FallbackText": "Australian Grown"}
            }
        ]

        cleaned_data = clean_raw_data_woolworths(
            raw_product_list=raw_product_list,
            company="Woolworths",
            store_id="5678",
            store_name="Test Woolies",
            state="VIC",
            category="fruit-veg",
            page_num=1,
            timestamp=datetime(2025, 8, 23)
        )

        self.assertEqual(len(cleaned_data['products']), 1)
        product = cleaned_data['products'][0]

        self.assertEqual(product['product_id_store'], '136341')
        self.assertEqual(product['barcode'], '0265178000003')
        self.assertEqual(product['name'], "Woolworths Bird's Eye Chilli Hot")
        self.assertEqual(product['brand'], 'Woolworths')
        self.assertEqual(product['price_current'], 0.14)
        self.assertFalse(product['is_on_special'])
        self.assertEqual(product['package_size'], 'each')
        self.assertEqual(product['country_of_origin'], 'Australia')
        self.assertEqual(product['health_star_rating'], 5.0)
        self.assertEqual(product['ingredients'], 'Chilli')
        self.assertEqual(product['allergens_may_be_present'], ['May contain traces of nuts'])
        self.assertEqual(product['category_path'], ['Fruit And Veg', 'Veg', 'Freshcuts', 'Hard Produce', 'Chillies', 'Chillies Loose'])
        self.assertIn('Australian Grown', product['tags'])
        self.assertEqual(product['rating_average'], 4.5)
        self.assertEqual(product['rating_count'], 10)
        self.assertEqual(mock_normalize.call_count, 1)

if __name__ == '__main__':
    unittest.main()
