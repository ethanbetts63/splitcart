
import json
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock
from decimal import Decimal

from django.test import TestCase, override_settings

from companies.models import Company, Division, Store
from products.models import Product, Price
from companies.tests.test_helpers.model_factories import CompanyFactory, DivisionFactory, StoreFactory
from api.utils.scraper_utils.clean_raw_data_woolworths import clean_raw_data_woolworths
from api.utils.database_updating_utils.consolidate_inbox_data import consolidate_inbox_data
from api.utils.database_updating_utils.update_database_from_consolidated_data import update_database_from_consolidated_data

RAW_WOOLWORTHS_PRODUCT = {
    "TileID": 0,
    "Stockcode": 136341,
    "Barcode": "0265178000003",
    "GtinFormat": 13,
    "CupPrice": 0.14,
    "InstoreCupPrice": 0.14,
    "CupMeasure": "1EA",
    "CupString": "$0.14 / 1EA",
    "InstoreCupString": "$0.14 / 1EA",
    "HasCupPrice": True,
    "InstoreHasCupPrice": True,
    "Price": 0.14,
    "IncrementalPrice": None,
    "IncrementalWasPrice": None,
    "IncrementalMinimumQuantity": None,
    "IncrementalMinimumQuantityUnit": "g",
    "PricePerKGLabel": None,
    "MinWeightPrice": None,
    "MaxWeightPrice": None,
    "InstorePrice": 0.14,
    "Name": "Woolworths Bird's Eye Chilli Hot",
    "DisplayName": "Woolworths Bird's Eye Chilli Hot each",
    "UrlFriendlyName": "woolworths-bird-s-eye-chilli-hot",
    "Description": " Woolworths Bird's Eye Chilli<br>Hot each",
    "SmallImageFile": "https://cdn1.woolworths.media/content/wowproductimages/small/136341.jpg",
    "MediumImageFile": "https://cdn1.woolworths.media/content/wowproductimages/medium/136341.jpg",
    "LargeImageFile": "https://cdn1.woolworths.media/content/wowproductimages/large/136341.jpg",
    "IsNew": False,
    "IsHalfPrice": False,
    "IsOnlineOnly": False,
    "IsOnSpecial": False,
    "InstoreIsOnSpecial": False,
    "IsEdrSpecial": False,
    "SavingsAmount": 0.0,
    "InstoreSavingsAmount": 0.0,
    "WasPrice": 0.14,
    "InstoreWasPrice": 0.14,
    "QuantityInTrolley": 0,
    "Unit": "Each",
    "MinimumQuantity": 1,
    "HasBeenBoughtBefore": False,
    "IsInTrolley": False,
    "Source": "Aisle.FruitVeg",
    "SupplyLimit": 36,
    "ProductLimit": 36,
    "MaxSupplyLimitMessage": "36 item limit",
    "IsRanged": True,
    "IsInStock": True,
    "PackageSize": "each",
    "IsPmDelivery": False,
    "IsForCollection": True,
    "IsForDelivery": True,
    "IsForExpress": True,
    "ProductRestrictionMessage": None,
    "ProductWarningMessage": None,
    "CentreTag": {
      "TagContent": None,
      "TagLink": None,
      "FallbackText": None,
      "TagType": "None",
      "MultibuyData": None,
      "MemberPriceData": None,
      "FFPVMemberPriceData": None,
      "TagContentText": None,
      "DualImageTagContent": None,
      "PromotionType": "NOT_SET",
      "IsRegisteredRewardCardPromotion": False
    },
    "IsCentreTag": False,
    "ImageTag": {
      "TagContent": "/content/promotiontags/australian-grown-roundel-200x200.png",
      "TagLink": None,
      "FallbackText": "Australian Grown",
      "TagType": "Image",
      "MultibuyData": None,
      "MemberPriceData": None,
      "FFPVMemberPriceData": None,
      "TagContentText": None,
      "DualImageTagContent": None,
      "PromotionType": "NOT_SET",
      "IsRegisteredRewardCardPromotion": False
    },
    "HeaderTag": None,
    "HasHeaderTag": False,
    "UnitWeightInGrams": 0,
    "SupplyLimitMessage": "test",
    "SmallFormatDescription": "Woolworths Bird's Eye Chilli Hot",
    "FullDescription": "Woolworths Bird's Eye Chilli Hot",
    "IsAvailable": True,
    "InstoreIsAvailable": True,
    "IsPurchasable": True,
    "InstoreIsPurchasable": True,
    "AgeRestricted": False,
    "DisplayQuantity": 1,
    "RichDescription": None,
    "HideWasSavedPrice": False,
    "SapCategories": None,
    "Brand": "Woolworths",
    "IsRestrictedByDeliveryMethod": False,
    "FooterTag": {
      "TagContent": None,
      "TagLink": None,
      "FallbackText": None,
      "TagType": "None",
      "MultibuyData": None,
      "MemberPriceData": None,
      "FFPVMemberPriceData": None,
      "TagContentText": None,
      "DualImageTagContent": None,
      "PromotionType": "NOT_SET",
      "IsRegisteredRewardCardPromotion": False
    },
    "IsFooterEnabled": False,
    "Diagnostics": "0",
    "IsBundle": False,
    "IsInFamily": False,
    "ChildProducts": None,
    "UrlOverride": None,
    "AdditionalAttributes": {
      "sapdepartmentname": "FRUIT AND VEG",
      "sapcategoryname": "VEG / FRESHCUTS / HARD PRODUCE",
      "sapsubcategoryname": "CHILLIES",
      "sapsegmentname": "CHILLIES LOOSE"
    },
    "DetailsImagePaths": [
      "https://cdn1.woolworths.media/content/wowproductimages/large/136341.jpg"
    ],
    "Variety": "Hot",
    "Rating": {
      "ReviewCount": 0,
      "RatingCount": 0,
      "RatingSum": 0,
      "OneStarCount": 0,
      "TwoStarCount": 0,
      "ThreeStarCount": 0,
      "FourStarCount": 0,
      "FiveStarCount": 0,
      "Average": 0,
      "OneStarPercentage": 0,
      "TwoStarPercentage": 0,
      "ThreeStarPercentage": 0,
      "FourStarPercentage": 0,
      "FiveStarPercentage": 0
    },
    "HasProductSubs": False,
    "IsSponsoredAd": False,
    "AdID": None,
    "AdIndex": None,
    "AdStatus": None,
    "IsMarketProduct": False,
    "IsGiftable": False,
    "Vendor": None,
    "Untraceable": False,
    "ThirdPartyProductInfo": None,
    "MarketFeatures": None,
    "MarketSpecifications": None,
    "SupplyLimitSource": "ProductLimit",
    "Tags": [
      {
        "Content": {
          "Type": "Roundel",
          "Position": "Top",
          "Attributes": {
            "ImagePath": "/content/promotiontags/australian-grown-roundel-200x200.png",
            "FallbackText": "Australian Grown"
          },
          "FFPVAttributes": None
        },
        "TemplateId": None,
        "Metadata": None
      }
    ],
    "IsPersonalisedByPurchaseHistory": False,
    "IsFromFacetedSearch": False,
    "NextAvailabilityDate": "2025-08-11T00:00:00.0000000Z",
    "NumberOfSubstitutes": 0,
    "IsPrimaryVariant": False,
    "VariantGroupId": 0,
    "HasVariants": False,
    "VariantTitle": None,
    "IsTobacco": False,
    "IsB2BExtendedRangeSapCategory": False,
    "IsFreeShipping": None,
    "FulfilmentStoreId": 1101,
    "B2BExtendedRange": None,
    "OfferId": None,
    "BundleProductGroups": None
  }

@override_settings(DEBUG=True)
class TestDataFlowWoolworths(TestCase):

    def setUp(self):
        self.company = CompanyFactory(name="Woolworths")
        self.division = DivisionFactory(company=self.company)
        self.store = StoreFactory(company=self.company, division=self.division, store_name="Woolworths Test Store", store_id="WOW:1234")
        self.temp_dir = tempfile.mkdtemp()
        self.inbox_path = os.path.join(self.temp_dir, 'product_inbox')
        os.makedirs(self.inbox_path, exist_ok=True)

        self.mock_command = Mock()
        self.mock_command.stdout.write = Mock()
        self.mock_command.style.SUCCESS = lambda x: x
        self.mock_command.style.WARNING = lambda x: x
        self.mock_command.style.ERROR = lambda x: x
        self.mock_command.style.SQL_FIELD = lambda x: x

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_woolworths_data_flow_from_inbox(self):
        # --- Stage 1: Create a realistic inbox file ---
        timestamp = datetime.now()
        cleaned_data_packet = clean_raw_data_woolworths(
            raw_product_list=[RAW_WOOLWORTHS_PRODUCT],
            company=self.company.name,
            store_id=self.store.store_id,
            store_name=self.store.store_name,
            state=self.store.state,
            timestamp=timestamp
        )

        inbox_file_path = os.path.join(self.inbox_path, "woolworths_test.jsonl")
        with open(inbox_file_path, 'w') as f:
            for product in cleaned_data_packet['products']:
                line_data = {"product": product, "metadata": cleaned_data_packet['metadata']}
                json.dump(line_data, f)
                f.write('\n')

        # --- Stage 2: Update Database ---
        consolidated_data, processed_files = consolidate_inbox_data(self.inbox_path, self.mock_command)
        update_database_from_consolidated_data(consolidated_data, processed_files, self.mock_command)

        # --- Stage 3: Assert Database State ---
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Price.objects.count(), 1)

        product1 = Product.objects.get(name="Woolworths Bird's Eye Chilli Hot")
        self.assertEqual(product1.brand, "Woolworths")
        self.assertEqual(product1.sizes, ["each"])
        self.assertEqual(product1.barcode, "0265178000003")
        
        price1 = Price.objects.get(product=product1)
        self.assertEqual(price1.store, self.store)
        self.assertEqual(price1.price, Decimal('0.14'))
        self.assertFalse(price1.is_on_special)
        self.assertTrue(price1.is_available)
