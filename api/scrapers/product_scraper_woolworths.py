import requests
import json
from datetime import datetime
from django.utils.text import slugify
from api.scrapers.base_product_scraper import BaseProductScraper
from api.utils.scraper_utils.DataCleanerWoolworths import DataCleanerWoolworths
from api.utils.scraper_utils.jsonl_writer import JsonlWriter

class ProductScraperWoolworths(BaseProductScraper):
    """
    A scraper for Woolworths stores.
    """

    def __init__(self, command, company: str, store_id: str, store_name: str, state: str, categories_to_fetch: list):
        super().__init__(command, company, store_id, store_name, state)
        self.session = None
        self.categories_to_fetch = categories_to_fetch

    def setup(self):
        """
        Initializes the requests.Session and the JsonlWriter.
        """
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://www.woolworths.com.au",
            "referer": "https://www.woolworths.com.au/shop/browse/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        })

        try:
            self.session.get("https://www.woolworths.com.au/", timeout=60)
        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"Failed to initialize session: {e}"))
            return

        store_name_slug = f"{slugify(self.store_name)}-{self.store_id}"
        self.jsonl_writer = JsonlWriter(self.company, store_name_slug, self.state)

    def get_work_items(self) -> list:
        """
        Returns the list of Woolworths categories to scrape.
        """
        return self.categories_to_fetch

    def fetch_data_for_item(self, item) -> list:
        """
        Fetches the raw product data for a single Woolworths category.
        """
        category_slug, category_id = item
        all_raw_products = []
        page_num = 1

        while True:
            api_url = "https://www.woolworths.com.au/apis/ui/browse/category"
            payload = {
                "categoryId": category_id, "pageNumber": page_num, "pageSize": 36,
                "sortType": "PriceAsc",
                "url": f"/shop/browse/{category_slug}?pageNumber={page_num}&sortBy=PriceAsc",
                "location": f"/shop/browse/{category_slug}?pageNumber={page_num}&sortBy=PriceAsc&filter=SoldBy(Woolworths)",
                "formatObject": f'{{"name":"{category_slug}"}}', "isSpecial": False, "isBundle": False,
                "isMobile": False, "filters": [{"Key": "SoldBy", "Items": [{"Term": "Woolworths"}]}],
                "token": "", "gpBoost": 0, "isHideUnavailableProducts": False,
                "isRegisteredRewardCardPromotion": False, "categoryVersion": "v2",
                "enableAdReRanking": False, "groupEdmVariants": False, "activePersonalizedViewType": "",
                "storeId": self.store_id
            }

            try:
                response = self.session.post(api_url, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                
                raw_products_on_page = [p for bundle in data.get("Bundles", []) if bundle and bundle.get("Products") for p in bundle["Products"]]

                if not raw_products_on_page:
                    break

                all_raw_products.extend(raw_products_on_page)

            except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                self.command.stderr.write(self.command.style.ERROR(f"Error fetching data for category {category_slug}: {e}"))
                break
            
            page_num += 1
        
        return all_raw_products

    def clean_raw_data(self, raw_data: list) -> dict:
        """
        Cleans the raw Woolworths product data.
        """
        cleaner = DataCleanerWoolworths(
            raw_product_list=raw_data,
            company=self.company,
            store_id=self.store_id,
            store_name=self.store_name,
            state=self.state,
            timestamp=datetime.now()
        )
        return cleaner.clean_data()