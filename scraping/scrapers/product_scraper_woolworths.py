import requests
from datetime import datetime
from django.utils.text import slugify
from scraping.scrapers.base_product_scraper import BaseProductScraper
from scraping.utils.product_scraping_utils.DataCleanerWoolworths import DataCleanerWoolworths
from scraping.utils.product_scraping_utils.jsonl_writer import JsonlWriter

class ProductScraperWoolworths(BaseProductScraper):
    """
    A scraper for Woolworths stores.
    """

    def __init__(self, command, company: str, store_id: str, store_name: str, state: str, categories_to_fetch: list):
        super().__init__(command, company, store_id, store_name, state)
        self.session = None
        self.EXCLUDED_CATEGORY_SLUGS = ["everyday-market", "cigarettes-tobacco"]
        self.categories_to_fetch = [
            cat for cat in categories_to_fetch if cat[0] not in self.EXCLUDED_CATEGORY_SLUGS
        ]

    def setup(self):
        """
        Initializes the requests.Session and the JsonlWriter.
        """
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'origin': 'https://www.woolworths.com.au',
            'referer': 'https://www.woolworths.com.au/',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        })

        try:
            self.session.get("https://www.woolworths.com.au/", timeout=20)
        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"Failed to initialize session: {e}"))
            return False

        store_name_slug = f"{slugify(self.store_name)}-{self.store_id}"
        self.jsonl_writer = JsonlWriter(self.company, store_name_slug, self.state)
        return True

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
                "isHideEverydayMarketProducts": True,
                "isRegisteredRewardCardPromotion": False, "categoryVersion": "v2",
                "enableAdReRanking": False, "groupEdmVariants": False, "activePersonalizedViewType": "",
                "storeId": self.store_id
            }

            response = self.session.post(api_url, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            raw_products_on_page = [p for bundle in data.get("Bundles", []) if bundle and bundle.get("Products") for p in bundle["Products"]]
            
            if not raw_products_on_page:
                break

            all_raw_products.extend(raw_products_on_page)
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
            timestamp=datetime.now(),
            brand_translations=self.brand_translations,
            product_translations=self.product_translations,
        )
        cleaned_data = cleaner.clean_data()
        return cleaned_data