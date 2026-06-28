# Removed: IGA Support & Store Selection

Preserved before removal. IGA was removed because it uses per-store pricing (not national),
which required special-casing throughout the codebase and drove the need for store selection.
Store selection was removed because without IGA all remaining companies (Coles, Woolworths, Aldi)
price nationally — no store picker needed.

---

# IGA — Complete Files

## scraping/scrapers/product_scraper_iga.py
```python
import requests
import json
import time
import random
import uuid
from datetime import datetime
from django.utils.text import slugify
from scraping.scrapers.base_product_scraper import BaseProductScraper
from scraping.utils.product_scraping_utils.DataCleanerIga import DataCleanerIga
from scraping.utils.product_scraping_utils.get_iga_categories import get_iga_categories
from scraping.utils.product_scraping_utils.jsonl_writer import JsonlWriter

class IgaScraper(BaseProductScraper):
    """
    A scraper for IGA stores.
    """
    def __init__(self, command, company: str, store_id: str, retailer_store_id: str, store_name: str, state: str):
        super().__init__(command, company, store_id, store_name, state)
        self.session = None
        self.retailer_store_id = retailer_store_id

    def setup(self):
        if not self.retailer_store_id:
            self.command.stderr.write(self.command.style.ERROR("Retailer store ID is missing."))
            return False

        self.session = requests.Session()
        self.session.headers.update({
            "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
            "x-shopping-mode": "11111111-1111-1111-1111-111111111111"
        })
        self.session.cookies.set("iga-shop.retailerStoreId", self.retailer_store_id)

        try:
            self.session.get("https://www.igashop.com.au/", timeout=60)
        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"Failed to initialize session: {e}"))
            return False

        store_name_slug = slugify(self.store_name.lower().replace('iga', '').replace('fresh', ''))
        self.jsonl_writer = JsonlWriter(self.company, store_name_slug, self.state)
        return True

    def get_work_items(self) -> list:
        return get_iga_categories(self.command, self.retailer_store_id, self.session)

    def fetch_data_for_item(self, item) -> list:
        category_identifier = item['identifier']
        all_raw_products = []
        session_id = str(uuid.uuid4())
        
        take = 36
        skip = 0
        previous_page_skus = set()

        while True:
            api_url = f"https://www.igashop.com.au/api/storefront/stores/{self.retailer_store_id}/categories/{requests.utils.quote(category_identifier)}/search"
            params = {'take': take, 'skip': skip, 'sessionId': session_id}

            try:
                response = self.session.get(api_url, params=params, timeout=60)
                if response.status_code == 404:
                    break
                response.raise_for_status()
                data = response.json()
                
                raw_products_on_page = data.get("items", [])
                if not raw_products_on_page:
                    break

                current_page_skus = {p.get('sku') for p in raw_products_on_page}
                if current_page_skus == previous_page_skus:
                    break
                previous_page_skus = current_page_skus

                all_raw_products.extend(raw_products_on_page)

            except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                self.command.stderr.write(self.command.style.ERROR(f"Error fetching data for category {category_identifier}: {e}"))
                break

            time.sleep(random.uniform(0.5, 1.5))
            skip += take
        
        return all_raw_products

    def clean_raw_data(self, raw_data: list) -> dict:
        cleaner = DataCleanerIga(
            raw_product_list=raw_data,
            company=self.company,
            store_id=self.store_id,
            store_name=self.store_name,
            state=self.state,
            timestamp=datetime.now(),
            brand_translations=self.brand_translations,
            product_translations=self.product_translations,
        )
        return cleaner.clean_data()
```

## scraping/scrapers/store_scraper_iga.py
```python
import json
import html
import re
from datetime import datetime
from scraping.scrapers.base_store_scraper import BaseStoreScraper
from scraping.utils.shop_scraping_utils.StoreCleanerIga import StoreCleanerIga
import requests

class StoreScraperIga(BaseStoreScraper):
    def __init__(self, command):
        super().__init__(command, 'iga')
        self.session = requests.Session()
        self.session.headers.update({
            "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
        })
        self.max_store_id = 23001

    def setup(self):
        self.stdout.write("\nPerforming thorough search for IGA stores...")

    def get_work_items(self) -> list:
        return list(range(1, self.max_store_id + 1))

    def fetch_data_for_item(self, item) -> list:
        store_id_num = item  
        url = f"https://embed.salefinder.com.au/location/storelocator/183/?format=json&saleGroup=0&limit=1500&locationId={store_id_num}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            jsonp_content = response.text
            start_index = jsonp_content.find('(')
            end_index = jsonp_content.rfind(')')
            if start_index != -1 and end_index != -1:
                json_str = jsonp_content[start_index + 1:end_index]
                data = json.loads(json_str)
                html_content = data.get('content', '')
                return self.parse_and_clean_stores(html_content)
        except (requests.exceptions.RequestException, json.JSONDecodeError, ValueError):
            pass
        return []

    def parse_and_clean_stores(self, html_content):
        stores = []
        store_data_matches = re.findall(r'data-storedata="([^"]*)"', html_content)
        for store_data_str in store_data_matches:
            decoded_str = html.unescape(store_data_str)
            try:
                store_data = json.loads(decoded_str)
                if 'distance' in store_data:
                    del store_data['distance']
                stores.append(store_data)
            except json.JSONDecodeError as e:
                self.stdout.write(f"\nError decoding JSON: {e}")
                self.stdout.write(f"Problematic string: {decoded_str}")
        return stores

    def clean_raw_data(self, raw_data: dict) -> dict:
        cleaner = StoreCleanerIga(raw_data, self.company, datetime.now())
        return cleaner.clean()

    def get_item_type(self) -> str:
        return "ID"

def find_iga_stores(command):
    scraper = StoreScraperIga(command)
    scraper.run()
```

## scraping/utils/product_scraping_utils/DataCleanerIga.py
```python
from datetime import datetime
from .BaseDataCleaner import BaseDataCleaner
from .field_maps import IGA_FIELD_MAP

class DataCleanerIga(BaseDataCleaner):
    def __init__(self, raw_product_list: list, company: str, store_name: str, store_id: str, state: str, timestamp: datetime, brand_translations: dict = None, product_translations: dict = None):
        super().__init__(raw_product_list, company, store_name, store_id, state, timestamp, brand_translations, product_translations)

    @property
    def field_map(self):
        return IGA_FIELD_MAP

    def _transform_product(self, raw_product: dict) -> dict:
        cleaned_product = {
            standard_field: self._get_value(raw_product, standard_field)
            for standard_field in self.field_map.keys()
        }

        was_price = raw_product.get('wasWholePrice')
        current_price = None
        if was_price:
            tpr_price_info = raw_product.get('tprPrice', [])
            if tpr_price_info:
                current_price = tpr_price_info[0].get('wholePrice')
        else:
            current_price = raw_product.get('wholePrice')

        if current_price is None:
            current_price = cleaned_product.get('price_current')

        price_info = self._calculate_price_info(current_price, was_price)
        cleaned_product.update(price_info)

        raw_breadcrumb = cleaned_product.get('category_path', '') or ''
        category_parts = [part for part in raw_breadcrumb.split('/') if part]
        cleaned_product['category_path'] = self._clean_category_path(category_parts)

        size_value = cleaned_product.get('size')
        size_type = raw_product.get('unitOfSize', {}).get('abbreviation')
        size_str = ""
        if size_value and size_type:
            size_str = f"{size_value}{size_type}"
        
        sell_by = raw_product.get('sellBy')
        if sell_by and sell_by != 'Each':
            size_str += f" {sell_by}"

        cleaned_product['size'] = size_str.strip()
        cleaned_product['is_available'] = raw_product.get('available', False)

        unit_of_measure = raw_product.get('unitOfMeasure', {})
        unit_of_size = raw_product.get('unitOfSize', {})
        measure_size = unit_of_measure.get('size')
        measure_abbr = unit_of_measure.get('abbreviation')
        product_size = unit_of_size.get('size')
        if measure_size and measure_abbr and product_size and current_price:
            cleaned_product['per_unit_price_value'] = current_price * (measure_size / product_size)
            cleaned_product['per_unit_price_measure'] = f"{measure_size}{measure_abbr}"

        unit_price_info = self._get_standardized_unit_price_info(cleaned_product)
        cleaned_product.update(unit_price_info)

        return cleaned_product
```

## scraping/utils/product_scraping_utils/get_iga_categories.py
```python
import requests
import json

_IGA_PROMOTIONAL_ROOTS = frozenset({
    'christmas',
    'seasonal',
    'specials',
    'promotions',
    'weekly specials',
})


def _find_leaf_categories(nodes: list, path: list = None) -> list:
    path = path or []
    leaf_categories = []
    for node in nodes:
        name = node.get('displayName') or ''
        if not path and name.lower() in _IGA_PROMOTIONAL_ROOTS:
            continue
        children = node.get('children', [])
        current_path = path + [name]
        if not children:
            if 'displayName' in node and 'identifier' in node:
                leaf_categories.append({
                    'displayName': node['displayName'],
                    'identifier': node['identifier'],
                })
        else:
            leaf_categories.extend(_find_leaf_categories(children, current_path))
    return leaf_categories

def get_iga_categories(command, retailer_store_id: str, session: requests.Session) -> list:
    command.stdout.write(f"    Fetching category hierarchy for store ID: {retailer_store_id}...")
    api_url = f"https://www.igashop.com.au/api/storefront/stores/{retailer_store_id}/categoryHierarchy"
    
    try:
        response = session.get(api_url, timeout=60)
        response.raise_for_status()
        hierarchy_data = response.json()
        root_nodes = hierarchy_data.get('children', [])
        leaf_categories = _find_leaf_categories(root_nodes)
        command.stdout.write(f"    Successfully extracted {len(leaf_categories)} specific subcategories.")
        return leaf_categories

    except requests.exceptions.RequestException as e:
        command.stdout.write(f"    ERROR: Could not fetch category hierarchy for store {retailer_store_id}. Error: {e}\n")
    except json.JSONDecodeError:
        command.stdout.write(f"    ERROR: Failed to decode JSON for category hierarchy for store {retailer_store_id}.")
    
    return []
```

## scraping/utils/shop_scraping_utils/StoreCleanerIga.py
```python
from datetime import datetime
from .BaseStoreCleaner import BaseStoreCleaner
from .store_field_maps import IGA_STORE_MAP

class StoreCleanerIga(BaseStoreCleaner):
    def __init__(self, raw_store_data: dict, company: str, timestamp: datetime):
        super().__init__(raw_store_data, company, timestamp)

    @property
    def field_map(self):
        return IGA_STORE_MAP

    def _transform_store(self) -> dict:
        cleaned_data = {
            standard_field: self._get_value(standard_field)
            for standard_field in self.field_map.keys()
        }
        raw_postcode = cleaned_data.get('postcode')
        if raw_postcode:
            cleaned_data['postcode'] = self._clean_postcode(str(raw_postcode))
        cleaned_data['is_active'] = True
        return cleaned_data
```

## scraping/tests/util_tests/test_get_iga_categories.py
```python
import pytest
from unittest.mock import MagicMock
from scraping.utils.product_scraping_utils.get_iga_categories import _find_leaf_categories, get_iga_categories


class TestFindLeafCategories:
    def test_empty_list(self):
        assert _find_leaf_categories([]) == []

    def test_single_leaf_node(self):
        nodes = [{'displayName': 'Dairy', 'identifier': 'cat-dairy', 'children': []}]
        result = _find_leaf_categories(nodes)
        assert result == [{'displayName': 'Dairy', 'identifier': 'cat-dairy'}]

    def test_nested_tree_returns_only_leaves(self):
        nodes = [
            {
                'displayName': 'Food', 'identifier': 'food', 'children': [
                    {'displayName': 'Dairy', 'identifier': 'dairy', 'children': []},
                    {'displayName': 'Bakery', 'identifier': 'bakery', 'children': []},
                ]
            }
        ]
        result = _find_leaf_categories(nodes)
        assert {'displayName': 'Dairy', 'identifier': 'dairy'} in result
        assert {'displayName': 'Bakery', 'identifier': 'bakery'} in result
        assert not any(r.get('displayName') == 'Food' for r in result)

    def test_node_missing_required_keys_excluded(self):
        nodes = [
            {'identifier': 'cat-1', 'children': []},
            {'displayName': 'Dairy', 'children': []},
        ]
        result = _find_leaf_categories(nodes)
        assert result == []


class TestGetIgaCategories:
    def test_returns_leaf_categories_from_api(self):
        command = MagicMock()
        session = MagicMock()
        session.get.return_value.json.return_value = {
            'children': [
                {'displayName': 'Dairy', 'identifier': 'dairy', 'children': []}
            ]
        }
        session.get.return_value.raise_for_status.return_value = None
        result = get_iga_categories(command, 'iga-001', session)
        assert {'displayName': 'Dairy', 'identifier': 'dairy'} in result

    def test_returns_empty_on_request_error(self):
        import requests
        command = MagicMock()
        session = MagicMock()
        session.get.side_effect = requests.exceptions.RequestException('error')
        result = get_iga_categories(command, 'iga-001', session)
        assert result == []

    def test_returns_empty_on_json_error(self):
        import json
        command = MagicMock()
        session = MagicMock()
        session.get.return_value.json.side_effect = json.JSONDecodeError('e', '', 0)
        session.get.return_value.raise_for_status.return_value = None
        result = get_iga_categories(command, 'iga-001', session)
        assert result == []
```

## scraping/tests/util_tests/test_store_cleaner_iga.py
```python
import pytest
from datetime import datetime
from scraping.utils.shop_scraping_utils.StoreCleanerIga import StoreCleanerIga


RAW_STORE = {
    'storeId': 'IGA001',
    'tag': 'iga-sydney',
    'storeName': 'IGA Sydney',
    'email': 'sydney@iga.com.au',
    'phone': '0212345678',
    'address': '123 Pitt St',
    'suburb': 'Sydney',
    'state': 'NSW',
    'postcode': '2000',
    'latitude': -33.87,
    'longitude': 151.21,
    'hours': {'mon': '7am-10pm'},
    'onlineShopUrl': 'https://shop.iga.com.au',
    'storeUrl': 'https://www.iga.com.au/stores/sydney',
    'ecommerceUrl': 'https://ecommerce.iga.com.au',
    'id': 'REC001',
    'status': 'active',
    'type': 'supermarket',
    'siteId': 'SITE001',
    'shoppingModes': ['instore', 'online'],
}


@pytest.fixture
def cleaner():
    return StoreCleanerIga(RAW_STORE, 'IGA', datetime(2024, 6, 15))


class TestTransformStore:
    def test_store_id_mapped(self, cleaner):
        result = cleaner._transform_store()
        assert result['store_id'] == 'IGA001'

    def test_store_name_mapped(self, cleaner):
        result = cleaner._transform_store()
        assert result['store_name'] == 'IGA Sydney'

    def test_postcode_cleaned(self, cleaner):
        result = cleaner._transform_store()
        assert result['postcode'] == '2000'

    def test_3_digit_postcode_padded(self):
        raw = {**RAW_STORE, 'postcode': '800'}
        cleaner = StoreCleanerIga(raw, 'IGA', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['postcode'] == '0800'

    def test_is_active_always_true(self, cleaner):
        result = cleaner._transform_store()
        assert result['is_active'] is True

    def test_state_mapped(self, cleaner):
        result = cleaner._transform_store()
        assert result['state'] == 'NSW'

    def test_suburb_mapped(self, cleaner):
        result = cleaner._transform_store()
        assert result['suburb'] == 'Sydney'
```

## scraping/tests/util_tests/test_data_cleaner_iga.py
```python
import pytest
from datetime import datetime
from scraping.utils.product_scraping_utils.DataCleanerIga import DataCleanerIga


@pytest.fixture
def cleaner():
    return DataCleanerIga(
        raw_product_list=[],
        company='IGA',
        store_name='IGA Test',
        store_id='IGA001',
        state='nsw',
        timestamp=datetime(2024, 6, 15),
        brand_translations={},
        product_translations={}
    )


RAW_PRODUCT_REGULAR = {
    'productId': 'P001',
    'name': 'Full Cream Milk',
    'brand': 'Pura',
    'barcode': '9310088000027',
    'description': 'Fresh milk',
    'priceNumeric': 2.80,
    'wasWholePrice': None,
    'tprPrice': [],
    'pricePerUnit': '$1.40 per 1L',
    'unitOfSize': {'size': 2, 'abbreviation': 'l'},
    'unitOfMeasure': {'size': 1, 'abbreviation': 'l'},
    'sellBy': 'Each',
    'available': True,
    'defaultCategory': [{'categoryBreadcrumb': 'Dairy/Milk/Full Cream'}],
}

RAW_PRODUCT_ON_SPECIAL = {
    'productId': 'P002',
    'name': 'Cheese Block',
    'brand': 'Bega',
    'barcode': None,
    'description': '',
    'priceNumeric': 5.00,
    'wasWholePrice': 7.00,
    'tprPrice': [{'wholePrice': 5.00}],
    'pricePerUnit': '$25.00 per 1kg',
    'unitOfSize': {'size': 200, 'abbreviation': 'g'},
    'unitOfMeasure': {'size': 100, 'abbreviation': 'g'},
    'sellBy': 'Each',
    'available': True,
    'defaultCategory': [{'categoryBreadcrumb': 'Dairy/Cheese'}],
}


class TestTransformProductPrice:
    def test_regular_price_not_on_special(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_REGULAR)
        assert result['price_current'] == 2.80
        assert result['is_on_special'] is False

    def test_special_price_taken_from_tpr(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_ON_SPECIAL)
        assert result['price_current'] == 5.00
        assert result['price_was'] == 7.00
        assert result['is_on_special'] is True
        assert result['price_save_amount'] == 2.00


class TestTransformProductSize:
    def test_size_string_constructed_from_unit_of_size(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_REGULAR)
        assert result['size'] == '2l'

    def test_sell_by_each_not_appended_to_size(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_REGULAR)
        assert 'Each' not in result['size']

    def test_sell_by_non_each_appended_to_size(self, cleaner):
        raw = {**RAW_PRODUCT_REGULAR, 'sellBy': 'Dozen'}
        result = cleaner._transform_product(raw)
        assert 'Dozen' in result['size']

    def test_size_grams(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_ON_SPECIAL)
        assert result['size'] == '200g'


class TestTransformProductCategoryPath:
    def test_category_split_from_breadcrumb_slash(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_REGULAR)
        assert 'Dairy' in result['category_path']
        assert 'Milk' in result['category_path']
        assert 'Full Cream' in result['category_path']

    def test_empty_breadcrumb_gives_empty_path(self, cleaner):
        raw = {**RAW_PRODUCT_REGULAR, 'defaultCategory': [{'categoryBreadcrumb': ''}]}
        result = cleaner._transform_product(raw)
        assert result['category_path'] == []


class TestTransformProductUnitPrice:
    def test_unit_price_calculated_numerically(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_REGULAR)
        assert result.get('per_unit_price_value') == pytest.approx(1.40)

    def test_unit_price_standardized_to_per_1l(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_REGULAR)
        assert result.get('unit_of_measure') == '1l'
        assert result.get('unit_price') == pytest.approx(1.40)

    def test_unit_price_per_1kg_for_grams_product(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_ON_SPECIAL)
        assert result.get('unit_of_measure') == '1kg'
        assert result.get('unit_price') == pytest.approx(25.00)
```

---

# IGA — Partial Excerpts

## scraping/utils/product_scraping_utils/field_maps.py
Lines 89–109 — IGA field map (delete this block; keep COLES_FIELD_MAP, WOOLWORTHS_FIELD_MAP, ALDI_FIELD_MAP):
```python
IGA_FIELD_MAP = {
    "sku": "productId",
    "name": "name",
    "brand": "brand",
    "barcode": "barcode",
    "description": "description",
    "ingredients": None,
    "allergens": None,
    "country_of_origin": None,
    "size": "unitOfSize.size",
    "url": None,
    "category_path": "defaultCategory.0.categoryBreadcrumb",
    "price_current": "priceNumeric",
    "price_was": None,
    "per_unit_price_string": "pricePerUnit",
    "per_unit_price_value": None,
    "per_unit_price_measure": None,
    "average_user_rating": None,
    "rating_count": None,
    "health_star_rating": None,
}
```

## scraping/management/commands/scrape.py
Line 10 — import to remove:
```python
from scraping.scrapers.product_scraper_iga import IgaScraper as ProductScraperIga
```
Line 31 — argument to remove:
```python
parser.add_argument('--iga', action='store_true', help='Limit the scheduler worker to IGA stores.')
```
Line 135 — companies_to_scrape append to remove:
```python
if options['iga']: companies_to_scrape.append('Iga')
```
Lines 207–211 — elif branch to remove from `_scrape_single_store`:
```python
elif company_name == "Iga":
    scraper = ProductScraperIga(
        command=self, company=store.company.name, store_id=store.store_id,
        retailer_store_id=store.retailer_store_id, store_name=store.store_name, state=store.state
    )
```

## scraping/management/commands/find_stores.py
Line 3 — import to remove:
```python
from scraping.scrapers.store_scraper_iga import find_iga_stores
```
Line 13 — argument to remove:
```python
parser.add_argument('--iga', action='store_true', help='Find IGA stores.')
```
Line 17 — `or options['iga']` to remove from any_specific_store check:
```python
any_specific_store = options['aldi'] or options['coles'] or options['iga'] or options['woolworths']
```
Lines 23–24 — unconditional call to remove:
```python
find_iga_stores(self)
```
Lines 35–38 — elif block to remove:
```python
if options['iga']:
    self.stdout.write(self.style.SUCCESS("--- Starting IGA store location scraping process ---"))
    find_iga_stores(self)
    self.stdout.write(self.style.SUCCESS("\n--- IGA store location scraping complete ---"))
```

## data_management/utils/path_classifier.py
Lines 160–165 — `_COMPANY_KEY_MAP`, remove the `'iga': 'Iga'` entry:
```python
_COMPANY_KEY_MAP = {
    'coles': 'Coles',
    'woolworths': 'Woolworths',
    'aldi': 'Aldi',
    'iga': 'Iga',   # <-- remove this line
}
```

## products/models/product_price_summary.py
Line 20 — field to remove:
```python
# The number of different IGA stores that stock this product.
iga_store_count = models.PositiveIntegerField(default=0)
```

## products/utils/get_pricing_stores.py
Lines 65–67 — IGA carve-out to remove (the surrounding fallback loop stays, just delete the IGA check):
```python
# For IGA, do nothing. Accept that it has no prices.
if store.company.name.lower() == 'iga':
    continue
```

## products/utils/bargain_utils.py
Lines 38–42 — IGA special case in `calculate_bargains` (simplifies to just `if len(company_ids) < 2: continue`):
```python
# A bargain must be between different companies or between different IGA stores
company_ids = {p.store.company_id for p in prices}
is_iga = any(p.store.company.name.lower() == 'iga' for p in prices)
iga_stores = {p.store_id for p in prices if p.store.company.name.lower() == 'iga'}

if len(company_ids) < 2 and (not is_iga or len(iga_stores) < 2):
    continue
```

## products/utils/product_ordering.py
Lines 61–64 — same IGA bargain exception (same simplification as above):
```python
company_ids = {p.store.company_id for p in prices}
is_iga = any(p.store.company.name.lower() == 'iga' for p in prices)
iga_stores = {p.store_id for p in prices if p.store.company.name.lower() == 'iga'}
if len(company_ids) < 2 and (not is_iga or len(iga_stores) < 2):
    continue
```

## data_management/utils/generation_utils/price_summaries_generator.py
Lines 48–58 — iga_store_count tracking and guard (simplifies to just `if company_count < 2: continue`):
```python
company_ids = set()
iga_store_count = 0
for p in prices:
    company_ids.add(p.store.company.id)
    if p.store.company.name.lower() == 'iga':
        iga_store_count += 1

company_count = len(company_ids)

if company_count < 2 and iga_store_count < 2:
    continue
```
Line 70 — remove `iga_store_count=iga_store_count` from the `ProductPriceSummary(...)` call.

## data_management/utils/generation_utils/bargain_stats_generator.py
Lines 29–35 — IGA average vs min logic (simplifies to `comparison_prices[name] = min(price_list)` for all):
```python
# Use average for IGA, min for others.
comparison_prices = {}
for name, price_list in prices_by_company.items():
    if name.lower() == 'iga':
        comparison_prices[name] = sum(price_list) / len(price_list)
    else:
        comparison_prices[name] = min(price_list)
```

## data_management/utils/geospatial_utils.py
Lines 58–62 — IGA unscraped store filter to remove (just delete these 4 lines):
```python
# Only include IGA stores that have been scraped at least once
all_stores = all_stores.filter(
    Q(company__name__iexact='IGA', last_scraped__isnull=False) | 
    ~Q(company__name__iexact='IGA')
)
```

## products/serializers/product_serializer.py
Lines 145–147 — IGA image resize block to remove:
```python
# --- Handle IGA (resize by changing URL parameters) ---
if company_name_lower == 'iga':
    return base_url.replace("w_500", "w_280").replace("h_500", "h_280")
```

## companies/models/store.py
Lines 129–136 — IGA-only field to remove (also needs a migration):
```python
# Company-specific fields

# IGA
retailer_store_id = models.CharField(
    max_length=50,
    blank=True,
    null=True,
    help_text="The retailer-specific identifier for the store, if available."
    # IGA: retailerStoreId
)
```

## data_management/analysers/internal_company_product_crossover.py
Lines 124–129 — IGA gets Tier 1 start categories instead of root (simplifies to just the else branch for all):
```python
if company.name.lower() == 'iga':
    level_name = "Tier 1"
    tier_0_categories_qs = Category.objects.filter(company=company, parents__isnull=True)
    start_categories = Category.objects.filter(parents__in=tier_0_categories_qs).distinct()
else:
    start_categories = Category.objects.filter(company=company, parents__isnull=True)
```

## scraping/tests/util_tests/test_normalization_e2e.py
Lines 351–360 — IGA cross-check tests to remove:
```python
def test_woolworths_and_iga_produce_same_key(self):
    assert self._get_key(DataCleanerWoolworths, self._WOW_MILK) == \
           self._get_key(DataCleanerIga, self._IGA_MILK)

def test_all_four_stores_produce_same_key(self):
    wow = self._get_key(DataCleanerWoolworths, self._WOW_MILK)
    col = self._get_key(DataCleanerColes, self._COLES_MILK)
    iga = self._get_key(DataCleanerIga, self._IGA_MILK)
    aldi = self._get_key(DataCleanerAldi, self._ALDI_MILK)
    assert wow == col == iga == aldi
```

## products/tests/util_tests/test_get_pricing_stores.py
Lines 68–81 — IGA fallback exemption test to remove:
```python
def test_unpriced_iga_store_stays_as_itself(self, make_anchored_store):
    iga = CompanyFactory(name='IGA')
    unpriced_iga_store = make_anchored_store(company=iga)

    other_anchor = StoreFactory(company=iga)
    extra_member = StoreFactory(company=iga)
    group = StoreGroup.objects.create(company=iga, anchor=other_anchor)
    StoreGroupMembership.objects.create(store=other_anchor, group=group)
    StoreGroupMembership.objects.create(store=extra_member, group=group)

    result = get_pricing_stores_map([unpriced_iga_store.id])

    assert result[unpriced_iga_store.id] == unpriced_iga_store.id
```

## products/tests/util_tests/test_bargain_utils.py
Lines 87–96 — IGA two-store bargain test to remove:
```python
def test_two_iga_stores_with_different_prices_is_a_bargain(self):
    iga = CompanyFactory(name='IGA')
    product = ProductFactory()
    store1 = StoreFactory(company=iga)
    store2 = StoreFactory(company=iga)
    PriceFactory(product=product, store=store1, price=Decimal('10.00'))
    PriceFactory(product=product, store=store2, price=Decimal('7.00'))

    result = calculate_bargains([product.id], [store1.id, store2.id])
```

## data_management/tests/util_tests/test_geospatial_utils.py
Lines 86–91 — IGA never-scraped exclusion test to remove:
```python
def test_excludes_iga_store_never_scraped(self):
    ref = PostcodeFactory(postcode='2600', latitude=-33.8688, longitude=151.2093)
    iga = CompanyFactory(name='IGA')
    iga_store = StoreFactory(company=iga, latitude=-33.8700, longitude=151.2090, last_scraped=None)
    result = get_nearby_stores(ref, radius_km=5)
    assert iga_store not in result
```

---

# Store Selection — Backend Complete Files

## users/models/selected_store_list.py
```python
import uuid
from django.db import models
from django.conf import settings
from companies.models import Store

class SelectedStoreList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='store_lists'
    )
    anonymous_id = models.UUIDField(null=True, blank=True, db_index=True)
    name = models.CharField(max_length=255, default="My Store List")
    is_user_defined = models.BooleanField(default=False)
    stores = models.ManyToManyField(Store, related_name='store_lists')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Selected Store List"
        verbose_name_plural = "Selected Store Lists"
        unique_together = ('user', 'name')

    def __str__(self):
        return f"{self.name} ({self.user.email if self.user else 'Anonymous'})"
```

## users/views/selected_store_list_viewset.py
```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from users.models import SelectedStoreList
from users.serializers import SelectedStoreListSerializer
from splitcart.permissions import IsAuthenticatedOrAnonymous

class SelectedStoreListViewSet(viewsets.ModelViewSet):
    serializer_class = SelectedStoreListSerializer
    permission_classes = [IsAuthenticatedOrAnonymous]
    queryset = SelectedStoreList.objects.all()
    lookup_field = 'pk'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        else:
            anonymous_id = getattr(self.request, 'anonymous_id', None) or self.request.query_params.get('anonymous_id')
            if anonymous_id:
                return self.queryset.filter(anonymous_id=anonymous_id)
            return self.queryset.none()

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            user = self.request.user
            base_name = "List"
            counter = 1
            existing_names = SelectedStoreList.objects.filter(user=user).values_list('name', flat=True)
            new_name = f"{base_name} {counter}"
            while new_name in existing_names:
                counter += 1
                new_name = f"{base_name} {counter}"
            serializer.save(user=user, name=new_name)
        else:
            anonymous_id = getattr(self.request, 'anonymous_id', None)
            serializer.save(anonymous_id=anonymous_id, name="My Stores")

    def update(self, request, *args, **kwargs):
        if 'stores' in request.data:
            request.data['is_user_defined'] = True
        if not request.user.is_authenticated and 'name' in request.data:
            raise PermissionDenied("Anonymous users cannot change the store list name.")
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request, *args, **kwargs):
        store_list = self.get_queryset().order_by('-last_used_at').first()
        if not store_list:
            return Response({'store_list': None}, status=status.HTTP_200_OK)
        serializer = self.get_serializer(store_list)
        return Response({'store_list': serializer.data}, status=status.HTTP_200_OK)
```

## users/views/nearby_store_list_view.py
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from companies.models import Postcode
from data_management.utils.geospatial_utils import get_nearby_stores
from companies.serializers.store_serializer import StoreSerializer

class NearbyStoreListView(APIView):
    def get(self, request, *args, **kwargs):
        postcode_param = request.query_params.get('postcode')
        radius_param = request.query_params.get('radius')
        companies_param = request.query_params.get('companies')

        if not postcode_param or not radius_param:
            return Response(
                {'error': 'Postcode and radius are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            radius = float(radius_param)
            postcode_list = [p.strip() for p in postcode_param.split(',')]
            all_nearby_stores = set()
            companies = companies_param.split(',') if companies_param else None

            for p_code in postcode_list:
                if not p_code: continue
                ref_postcode = Postcode.objects.filter(postcode=p_code).first()
                if ref_postcode:
                    nearby_stores = get_nearby_stores(ref_postcode, radius, companies=companies)
                    all_nearby_stores.update(nearby_stores)
            
            stores_list = list(all_nearby_stores)
            store_serializer = StoreSerializer(stores_list, many=True)
            return Response({'stores': store_serializer.data}, status=status.HTTP_200_OK)

        except ValueError:
            return Response({'error': 'Invalid radius.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'An unexpected error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

## users/serializers/selected_store_list_serializer.py
```python
from rest_framework import serializers
from users.models import SelectedStoreList
from companies.models import Store

class SelectedStoreListSerializer(serializers.ModelSerializer):
    stores = serializers.PrimaryKeyRelatedField(many=True, queryset=Store.objects.all())

    class Meta:
        model = SelectedStoreList
        fields = ('id', 'name', 'stores', 'is_user_defined', 'created_at', 'updated_at', 'last_used_at')
        read_only_fields = ('created_at', 'updated_at', 'last_used_at')
```

## users/utils/session_merger.py
```python
from users.models import Cart, SelectedStoreList
from .name_generator import generate_unique_name

def merge_anonymous_session(user, anonymous_id):
    if not user or not anonymous_id:
        return

    try:
        anon_cart = Cart.objects.get(anonymous_id=anonymous_id, is_active=True)
        anon_list = anon_cart.selected_store_list

        Cart.objects.filter(user=user, is_active=True).update(is_active=False)

        new_list_name = "My Store List"
        if anon_list and anon_list.name != 'Default List':
            new_list_name = anon_list.name
        
        unique_list_name = generate_unique_name(SelectedStoreList, {'user': user}, new_list_name)
        new_list = SelectedStoreList.objects.create(user=user, name=unique_list_name)
        if anon_list:
            new_list.stores.set(anon_list.stores.all())

        new_cart_name = "Cart"
        if anon_cart.name != 'Anonymous Cart':
            new_cart_name = anon_cart.name

        unique_cart_name = generate_unique_name(Cart, {'user': user}, new_cart_name)
        new_cart = Cart.objects.create(
            user=user, 
            name=unique_cart_name, 
            is_active=True, 
            selected_store_list=new_list
        )

        anon_cart.items.update(cart=new_cart)
        anon_cart.delete()
        if anon_list:
            anon_list.delete()

    except Cart.DoesNotExist:
        pass
```

## users/utils/name_generator.py
```python
def generate_unique_name(model_class, owner_filter, base_name):
    if not model_class.objects.filter(**owner_filter, name=base_name).exists():
        return base_name

    i = 1
    while True:
        name = f"{base_name} #{i}"
        if not model_class.objects.filter(**owner_filter, name=name).exists():
            return name
        i += 1
```

## users/utils/cart_optimization.py
```python
from rest_framework.response import Response
from rest_framework import status
from companies.models import Store
from data_management.utils.cart_optimization import calculate_optimized_cost, calculate_baseline_cost, build_price_slots, calculate_best_single_store
from products.utils.get_pricing_stores import get_pricing_stores_map
from users.models import Cart


def _translate_shopping_plan(shopping_plan, anchor_name_to_original):
    translated = {}
    for anchor_name, plan_data in shopping_plan.items():
        originals = anchor_name_to_original.get(anchor_name, [])
        new_entry = dict(plan_data)
        if originals:
            store_options = []
            for s in originals:
                addr_parts = [s.address_line_1, s.suburb, s.state, s.postcode]
                store_options.append({
                    'store_name': s.store_name,
                    'store_address': ', '.join(part for part in addr_parts if part),
                })
            new_entry['store_options'] = store_options
            new_entry['store_address'] = store_options[0]['store_address']
            new_key = store_options[0]['store_name']
        else:
            new_entry['store_options'] = []
            new_key = anchor_name
        translated[new_key] = new_entry
    return translated


def run_cart_optimization(cart_obj, store_list, max_stores_options):
    if not store_list:
        return Response({'error': 'A store list is required for optimization.'}, status=status.HTTP_400_BAD_REQUEST)

    store_ids = list(store_list.stores.values_list('id', flat=True))
    if not store_ids:
        return Response({'error': 'No stores selected in the provided store list.'}, status=status.HTTP_400_BAD_REQUEST)

    pricing_map = get_pricing_stores_map(store_ids)
    pricing_store_ids = list(set(pricing_map.values()))
    stores = Store.objects.filter(id__in=pricing_store_ids)

    anchor_to_selected_ids = {}
    for selected_id, anchor_id in pricing_map.items():
        anchor_to_selected_ids.setdefault(anchor_id, []).append(selected_id)
    original_store_map = {s.id: s for s in Store.objects.filter(id__in=store_ids)}
    anchor_name_to_original = {
        anchor.store_name: [
            original_store_map[sid]
            for sid in anchor_to_selected_ids.get(anchor.id, [])
            if sid in original_store_map
        ]
        for anchor in stores
    }

    original_items = []
    cart_with_substitutes_slots = []
    for item in cart_obj.items.all():
        original_items.append({'product': {'id': item.product.id}, 'quantity': item.quantity})
        approved_subs = item.chosen_substitutions.filter(is_approved=True)
        slot = []
        if approved_subs.exists():
            for sub in approved_subs:
                slot.append({'product_id': sub.substituted_product.id, 'quantity': sub.quantity})
        else:
            slot.append({'product_id': item.product.id, 'quantity': item.quantity})
        cart_with_substitutes_slots.append(slot)

    try:
        simple_cart = [[{'product_id': item['product']['id'], 'quantity': item['quantity']}] for item in original_items]
        simple_price_slots = build_price_slots(simple_cart, stores)
        if not simple_price_slots:
            return Response({'error': 'Could not find prices for the original items in your cart at the specified stores.'}, status=status.HTTP_404_NOT_FOUND)
        baseline_cost = calculate_baseline_cost(simple_price_slots)

        subs_price_slots = build_price_slots(cart_with_substitutes_slots, stores)
        subs_optimization_results = []
        if subs_price_slots:
            for max_stores in max_stores_options:
                optimized_cost, shopping_plan, _ = calculate_optimized_cost(subs_price_slots, max_stores)
                if optimized_cost is not None:
                    actual_stores_used = sum(1 for store_plan in shopping_plan.values() if store_plan['items'])
                    if actual_stores_used == max_stores:
                        savings = baseline_cost - optimized_cost if baseline_cost > 0 else 0
                        subs_optimization_results.append({
                            'max_stores': max_stores,
                            'optimized_cost': optimized_cost,
                            'savings': savings,
                            'shopping_plan': _translate_shopping_plan(shopping_plan, anchor_name_to_original),
                        })
            subs_best_single_store = calculate_best_single_store(subs_price_slots, cart_with_substitutes_slots)
            if subs_best_single_store:
                subs_best_single_store['shopping_plan'] = _translate_shopping_plan(subs_best_single_store['shopping_plan'], anchor_name_to_original)
        else:
            subs_best_single_store = None

        response_data = {
            'baseline_cost': baseline_cost,
            'optimization_results': subs_optimization_results,
            'best_single_store': subs_best_single_store,
        }

        no_subs_optimization_results = []
        for max_stores in max_stores_options:
            optimized_cost, shopping_plan, _ = calculate_optimized_cost(simple_price_slots, max_stores)
            if optimized_cost is not None:
                actual_stores_used = sum(1 for store_plan in shopping_plan.values() if store_plan['items'])
                if actual_stores_used == max_stores:
                    savings = baseline_cost - optimized_cost if baseline_cost > 0 else 0
                    no_subs_optimization_results.append({
                        'max_stores': max_stores,
                        'optimized_cost': optimized_cost,
                        'savings': savings,
                        'shopping_plan': _translate_shopping_plan(shopping_plan, anchor_name_to_original),
                    })

        no_subs_best_single_store = calculate_best_single_store(simple_price_slots, simple_cart)
        if no_subs_best_single_store:
            no_subs_best_single_store['shopping_plan'] = _translate_shopping_plan(no_subs_best_single_store['shopping_plan'], anchor_name_to_original)

        response_data['no_subs_results'] = {
            'baseline_cost': baseline_cost,
            'optimization_results': no_subs_optimization_results,
            'best_single_store': no_subs_best_single_store,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'An unexpected error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

# Store Selection — Backend Partial Excerpts

## users/models/cart.py
Lines 18–24 — FK to remove (also needs a migration):
```python
selected_store_list = models.ForeignKey(
    SelectedStoreList,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='carts'
)
```
Also remove the import at line 4: `from users.models.selected_store_list import SelectedStoreList`

## users/views/cart_viewset.py
Lines 60–65 — store list association on cart creation to remove from `perform_create`:
```python
# Associate with the most recent store list
store_list_owner_filter = {'user': user} if user else {'anonymous_id': anonymous_id}
store_list = SelectedStoreList.objects.filter(**store_list_owner_filter).order_by('-last_used_at').first()
if store_list:
    cart.selected_store_list = store_list
    cart.save()
```
Lines 97–105 — same in `active` action to remove:
```python
if created:
    store_list = None
    if user.is_authenticated:
        store_list = SelectedStoreList.objects.filter(user=user).order_by('-last_used_at').first()
    elif hasattr(request, 'anonymous_id'):
        store_list = SelectedStoreList.objects.filter(anonymous_id=request.anonymous_id).order_by('-last_used_at').first()
    if store_list:
        cart.selected_store_list = store_list
        cart.save()
```
Lines 170–181 — lazy-link in `sync` to remove:
```python
if not cart.selected_store_list:
    user = request.user
    owner_filter = {'user': user} if user.is_authenticated else {'anonymous_id': getattr(request, 'anonymous_id', None)}
    if any(v is not None for v in owner_filter.values()):
        store_list = SelectedStoreList.objects.filter(**owner_filter).order_by('-last_used_at').first()
        if store_list:
            cart.selected_store_list = store_list
            cart.save(update_fields=['selected_store_list'])
```
Lines 247–252 — substitute creation gated on store list to simplify:
```python
if cart.selected_store_list:
    store_ids = list(cart.selected_store_list.stores.values_list('id', flat=True))
    if store_ids:
        for item in created_items:
            manager = SubstituteManager(product_id=item.product.id, store_ids=store_ids)
            manager.create_cart_substitutions(original_cart_item=item)
```
Lines 265–277 — `optimize` action to remove entirely:
```python
@action(detail=True, methods=['post'], url_path='optimize')
def optimize(self, request, *args, **kwargs):
    cart_obj = self.get_object()
    store_list = cart_obj.selected_store_list
    if not store_list:
        return Response({'error': 'No store list linked to this cart.'}, status=status.HTTP_400_BAD_REQUEST)
    max_stores_options = request.data.get('max_stores_options', [2, 3, 4])
    return run_cart_optimization(cart_obj, store_list, max_stores_options)
```

## users/urls.py
Lines to remove:
```python
from users.views.selected_store_list_viewset import SelectedStoreListViewSet
from .views.nearby_store_list_view import NearbyStoreListView

router.register(r'store-lists', SelectedStoreListViewSet, basename='storelist')

path('stores/nearby/', NearbyStoreListView.as_view(), name='store-list'),
```

---

# Store Selection — Frontend Complete Files

## frontend/src/context/StoreListContext.tsx
```tsx
import { createContext, useContext, useState, type ReactNode, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from './AuthContext';
import { type SelectedStoreListType } from '../types';
import type { StoreListContextType } from '../types/StoreListContextType';
import * as storeListApi from '../services/storeList.api';
import { createApiClient } from '../services/apiClient';

const StoreListContext = createContext<StoreListContextType | undefined>(undefined);

export const StoreListProvider = ({ children }: { children: ReactNode }) => {
  const { token, anonymousId, isLoading: isAuthLoading } = useAuth();
  const apiClient = useMemo(() => createApiClient(token, anonymousId), [token, anonymousId]);

  const [selectedStoreIds, setSelectedStoreIds] = useState<Set<number>>(() => new Set<number>());
  const [currentStoreListId, setCurrentStoreListId] = useState<string | null>(null);
  const [currentStoreListName, setCurrentStoreListName] = useState<string>("");
  const [isUserDefinedList, setIsUserDefinedList] = useState<boolean>(false);
  const [userStoreLists, setUserStoreLists] = useState<SelectedStoreListType[]>([]);
  const [storeListLoading, setStoreListLoading] = useState<boolean>(true);
  const [storeListError, setStoreListError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInitialData = async () => {
      if (isAuthLoading) return;
      setStoreListLoading(true);
      try {
        const activeData = await storeListApi.fetchActiveStoreListDataAPI(apiClient);
        const storeList = activeData?.store_list ?? null;
        if (storeList) {
            setUserStoreLists([storeList]);
            setCurrentStoreListId(storeList.id);
            setCurrentStoreListName(storeList.name);
            setIsUserDefinedList(storeList.is_user_defined);
            setSelectedStoreIds(new Set(storeList.stores));
        } else {
            setCurrentStoreListId(null);
            setSelectedStoreIds(new Set());
        }
      } catch (error: any) {
        console.error("Failed to fetch initial store list data:", error);
        setStoreListError("Could not load initial store data.");
      } finally {
        setStoreListLoading(false);
      }
    };
    fetchInitialData();
  }, [apiClient, isAuthLoading]);

  useEffect(() => {
    if (storeListLoading || !currentStoreListId) return;
    saveStoreList(currentStoreListName, Array.from(selectedStoreIds));
  }, [selectedStoreIds]);

  const handleStoreSelect = (storeId: number) => {
    setSelectedStoreIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(storeId)) { newSet.delete(storeId); } else { newSet.add(storeId); }
      return newSet;
    });
  };

  const loadStoreList = useCallback(async (storeListId: string) => {
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      const data = await storeListApi.loadStoreListAPI(apiClient, storeListId);
      setCurrentStoreListId(data.id);
      setCurrentStoreListName(data.name);
      setSelectedStoreIds(new Set(data.stores));
      setIsUserDefinedList(data.is_user_defined);
    } catch (err: any) { setStoreListError(err.message); }
    finally { setStoreListLoading(false); }
  }, [apiClient]);

  const createNewStoreList = useCallback(async (storeIds: number[]) => {
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      const data = await storeListApi.createNewStoreListAPI(apiClient, storeIds);
      setCurrentStoreListId(data.id);
      setCurrentStoreListName(data.name);
      setSelectedStoreIds(new Set(data.stores));
      setIsUserDefinedList(data.is_user_defined);
      setUserStoreLists(prevLists => [...prevLists, data]);
    } catch (err: any) { setStoreListError(err.message); }
    finally { setStoreListLoading(false); }
  }, [apiClient]);

  const saveStoreList = useCallback(async (name: string, storeIds: number[]) => {
    if (!currentStoreListId) {
        if (storeIds.length > 0) { await createNewStoreList(storeIds); }
        return;
    }
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      const data = await storeListApi.saveStoreListAPI(apiClient, currentStoreListId, name, storeIds);
      setCurrentStoreListName(data.name);
      setIsUserDefinedList(data.is_user_defined);
      setUserStoreLists(prev => prev.map(list => list.id === data.id ? data : list));
    } catch (err: any) { setStoreListError(err.message); }
    finally { setStoreListLoading(false); }
  }, [apiClient, currentStoreListId, createNewStoreList]);

  const deleteStoreList = useCallback(async (storeListId: string) => {
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      await storeListApi.deleteStoreListAPI(apiClient, storeListId);
      const remainingLists = userStoreLists.filter(list => list.id !== storeListId);
      setUserStoreLists(remainingLists);
      if (currentStoreListId === storeListId) {
        if (remainingLists.length > 0) {
          const nextActiveList = remainingLists.sort((a, b) => new Date(b.last_used_at).getTime() - new Date(a.last_used_at).getTime())[0];
          await loadStoreList(nextActiveList.id);
        } else {
          await createNewStoreList([]);
        }
      }
    } catch (err: any) { setStoreListError(err.message); }
    finally { setStoreListLoading(false); }
  }, [apiClient, currentStoreListId, userStoreLists, loadStoreList, createNewStoreList]);

  const contextValue = {
    selectedStoreIds, setSelectedStoreIds, handleStoreSelect,
    currentStoreListId, setCurrentStoreListId,
    currentStoreListName, setCurrentStoreListName,
    isUserDefinedList, userStoreLists, setUserStoreLists,
    storeListLoading, setStoreListLoading, storeListError, setStoreListError,
    loadStoreList, saveStoreList, createNewStoreList, deleteStoreList,
    fetchActiveStoreList: async () => { console.warn("fetchActiveStoreList is deprecated"); },
  };

  return (
    <StoreListContext.Provider value={contextValue}>
      {children}
    </StoreListContext.Provider>
  );
};

export const useStoreList = () => {
  const context = useContext(StoreListContext);
  if (context === undefined) throw new Error('useStoreList must be used within a StoreListProvider');
  return context;
};
```

## frontend/src/context/StoreSearchContext.tsx
```tsx
import { createContext, useContext, useState, type ReactNode, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from './AuthContext';
import { createApiClient } from '../services/apiClient';
import { searchNearbyStoresAPI } from '../services/store.api';
import { companyNames } from '../lib/companies';
import type { Store } from '../types/Store';
import type { MapBounds } from '../types/MapBounds';
import type { StoreSearchContextType } from '../types/StoreSearchContextType';

const StoreSearchContext = createContext<StoreSearchContextType | undefined>(undefined);

export const StoreSearchProvider = ({ children }: { children: ReactNode }) => {
  const { token, anonymousId } = useAuth();
  const apiClient = useMemo(() => createApiClient(token, anonymousId), [token, anonymousId]);

  const [stores, setStores] = useState<Store[] | null>(() => {
    if (typeof window === 'undefined') return null;
    const saved = sessionStorage.getItem('stores');
    return saved ? JSON.parse(saved) : null;
  });

  useEffect(() => { if (stores) { sessionStorage.setItem('stores', JSON.stringify(stores)); } }, [stores]);
  const [postcode, setPostcode] = useState(() => { if (typeof window === 'undefined') return ''; return sessionStorage.getItem('postcode') || ''; });
  useEffect(() => { sessionStorage.setItem('postcode', postcode); }, [postcode]);
  const [radius, setRadius] = useState(() => { if (typeof window === 'undefined') return 5; const saved = sessionStorage.getItem('radius'); return saved ? JSON.parse(saved) : 5; });
  useEffect(() => { sessionStorage.setItem('radius', JSON.stringify(radius)); }, [radius]);
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>(() => { return [...companyNames]; });
  useEffect(() => { sessionStorage.setItem('selectedCompanies', JSON.stringify(selectedCompanies)); }, [selectedCompanies]);

  const [mapBounds, setMapBounds] = useState<MapBounds>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = useCallback(async (): Promise<Store[] | null> => {
    if (!postcode || postcode.split(',').some(p => !/^\d{4}$/.test(p.trim()))) {
      setError("Please enter valid 4-digit postcodes.");
      return null;
    }
    setIsLoading(true);
    setError(null);
    try {
      const data = await searchNearbyStoresAPI(apiClient, { postcode, radius, companies: selectedCompanies });
      const fetchedStores = data.stores || [];
      setStores(fetchedStores);
      if (fetchedStores.length > 0) {
        const bounds = fetchedStores.reduce((acc, store) => {
          return [[Math.min(acc[0][0], store.latitude), Math.min(acc[0][1], store.longitude)], [Math.max(acc[1][0], store.latitude), Math.max(acc[1][1], store.longitude)]];
        }, [[fetchedStores[0].latitude, fetchedStores[0].longitude], [fetchedStores[0].latitude, fetchedStores[0].longitude]]) as [[number, number], [number, number]];
        setMapBounds(bounds);
      } else { setMapBounds(null); }
      return fetchedStores;
    } catch (err: any) { setError(err.message); setStores([]); return null; }
    finally { setIsLoading(false); }
  }, [apiClient, postcode, radius, selectedCompanies, setStores, setMapBounds]);

  return (
    <StoreSearchContext.Provider value={{ stores, setStores, postcode, setPostcode, radius, setRadius, selectedCompanies, setSelectedCompanies, mapBounds, setMapBounds, isLoading, error, handleSearch }}>
      {children}
    </StoreSearchContext.Provider>
  );
};

export const useStoreSearch = () => {
  const context = useContext(StoreSearchContext);
  if (context === undefined) throw new Error('useStoreSearch must be used within a StoreSearchProvider');
  return context;
};
```

## frontend/src/services/storeList.api.ts
```ts
import { type SelectedStoreListType } from '../types';
import type { ActiveStoreListData } from '../types/ActiveStoreListData';
import { type ApiClient } from './apiClient';

export const fetchActiveStoreListDataAPI = (apiClient: ApiClient): Promise<ActiveStoreListData> => {
  return apiClient.get<ActiveStoreListData>('/api/store-lists/active/');
};

export const fetchUserStoreListsAPI = async (apiClient: ApiClient): Promise<SelectedStoreListType[]> => {
  const url = '/api/store-lists/';
  const data = await apiClient.get<SelectedStoreListType[] | { results: SelectedStoreListType[] }>(url);
  if (data && typeof data === 'object' && 'results' in data && Array.isArray(data.results)) return data.results;
  if (Array.isArray(data)) return data;
  console.error("API response for store lists was not in the expected format:", data);
  return [];
};

export const loadStoreListAPI = (apiClient: ApiClient, storeListId: string): Promise<SelectedStoreListType> => {
    return apiClient.get<SelectedStoreListType>(`/api/store-lists/${storeListId}/`);
};

export const saveStoreListAPI = (apiClient: ApiClient, listId: string | null, name: string, storeIds: number[]): Promise<SelectedStoreListType> => {
    const method = listId ? 'PUT' : 'POST';
    const url = listId ? `/api/store-lists/${listId}/` : '/api/store-lists/';
    const requestBody: { name?: string; stores: number[] } = { stores: storeIds };
    if (apiClient.isAuthenticated()) { requestBody.name = name; }
    if (method === 'PUT') { return apiClient.put<SelectedStoreListType>(url, requestBody); }
    else { return apiClient.post<SelectedStoreListType>(url, requestBody); }
};

export const createNewStoreListAPI = (apiClient: ApiClient, storeIds: number[]): Promise<SelectedStoreListType> => {
    return apiClient.post<SelectedStoreListType>('/api/store-lists/', { stores: storeIds });
};

export const deleteStoreListAPI = (apiClient: ApiClient, storeListId: string): Promise<void> => {
    return apiClient.delete(`/api/store-lists/${storeListId}/`);
};
```

## frontend/src/services/store.api.ts
```ts
import { type ApiClient } from './apiClient';
import type { NearbyStoresResponse } from '../types/NearbyStoresResponse';
import type { SearchParams } from '../types/SearchParams';

export const searchNearbyStoresAPI = (apiClient: ApiClient, { postcode, radius, companies }: SearchParams): Promise<NearbyStoresResponse> => {
    const params = new URLSearchParams();
    params.append('postcode', postcode);
    params.append('radius', radius.toString());
    if (companies.length > 0) { params.append('companies', companies.join(',')); }
    return apiClient.get<NearbyStoresResponse>(`/api/stores/nearby/?${params.toString()}`);
};
```

## frontend/src/components/NavLocationButton.tsx
```tsx
"use client";

import { MapPin } from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { useStoreList } from "@/context/StoreListContext";
import { useDialog } from "@/context/DialogContext";

export function NavLocationButton() {
  const { selectedStoreIds, isUserDefinedList } = useStoreList();
  const { openDialog } = useDialog();

  return (
    <div className="relative">
      <Button variant="ghost" size="icon" className="h-10 w-10 sm:h-12 sm:w-12" onClick={() => openDialog("Edit Location")}>
        <MapPin className="size-6 sm:size-7" />
        <span className="sr-only">Edit Location</span>
      </Button>
      {isUserDefinedList && selectedStoreIds.size > 0 && (
        <Badge className="absolute -right-1 -top-1 h-5 min-w-5 justify-center rounded-full bg-blue-500 px-1 font-mono tabular-nums text-white">
          {selectedStoreIds.size}
        </Badge>
      )}
    </div>
  );
}
```

## frontend/src/components/StoreList.tsx
```tsx
"use client";

import { memo } from 'react';
import { Checkbox } from "./ui/checkbox";
import { Card, CardContent } from "./ui/card";
import { useCompanyLogo } from '../hooks/useCompanyLogo';
import { Skeleton } from './ui/skeleton';
import type { StoreListProps } from '../types/StoreListProps';

const StoreLogo = ({ companyName }: { companyName: string }) => {
  const { objectUrl, isLoading, error } = useCompanyLogo(companyName);
  if (isLoading) return <Skeleton className="h-4 w-10" />;
  if (error || !objectUrl) return <div className="h-4 w-10 flex items-center justify-center text-xs text-red-500">?</div>;
  return <img src={objectUrl} alt={companyName} className="h-4 w-auto" />;
};

const StoreList = ({ stores, selectedStoreIds, onStoreSelect }: StoreListProps) => {
  return (
    <div className="flex flex-col gap-2">
      {stores.map(store => {
        const isSelected = selectedStoreIds.has(store.id);
        return (
          <Card key={store.id} onClick={() => onStoreSelect(store.id)} className="cursor-pointer hover:bg-accent transition-colors py-1">
            <CardContent className="px-1 py-0.5 flex items-center gap-2">
              <div onClick={(e) => e.stopPropagation()}>
                <Checkbox checked={isSelected} onCheckedChange={() => onStoreSelect(store.id)} aria-label={`Select ${store.store_name}`} />
              </div>
              <StoreLogo companyName={store.company_name} />
              <span className="font-medium text-sm truncate">{store.store_name}</span>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

export default memo(StoreList);
```

## frontend/src/components/StoreMap.tsx
```tsx
import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, useMap } from 'react-leaflet';
import L from 'leaflet';
import type { Store } from '../types';
import { useCompanyLogo } from '../hooks/useCompanyLogo';
import type { MapBounds } from '../types/MapBounds';
import type { StoreMapProps } from '../types/StoreMapProps';

const markerHtmlStyles = `
  .map-logo-icon { background: transparent; border: none; }
  .map-logo-icon img { width: 35px; height: 35px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.5); transition: all 0.2s ease-in-out; }
  .desaturated img { filter: grayscale(100%); opacity: 0.6; }
  .map-logo-icon.selected img { border-color: #3b82f6; transform: scale(1.2); }
`;

const MapViewController: React.FC<{ bounds: MapBounds }> = ({ bounds }) => {
  const map = useMap();
  useEffect(() => { if (bounds) { map.fitBounds(bounds, { padding: [50, 50] }); } }, [bounds, map]);
  return null;
};

const StoreMarker: React.FC<{ store: Store; isSelected: boolean; onStoreSelect: (id: number) => void; onMouseOver: (name: string) => void; onMouseOut: () => void; }> = ({ store, isSelected, onStoreSelect, onMouseOver, onMouseOut }) => {
  const { objectUrl, isLoading } = useCompanyLogo(store.company_name);
  if (isLoading || !objectUrl) return null;
  const icon = L.divIcon({ html: `<img src="${objectUrl}" alt="${store.company_name} logo">`, className: `map-logo-icon ${isSelected ? 'selected' : 'desaturated'}`, iconSize: [35, 35], iconAnchor: [17, 35] });
  return (
    <Marker key={store.id} position={[store.latitude, store.longitude]} icon={icon}
      eventHandlers={{ click: () => onStoreSelect(store.id), mouseover: () => onMouseOver(store.store_name), mouseout: onMouseOut }} />
  );
};

const StoreMap: React.FC<StoreMapProps> = ({ bounds, stores, selectedStoreIds, onStoreSelect }) => {
    const [hoveredStoreName, setHoveredStoreName] = useState<string | null>(null);
    return (
        <div style={{ height: '100%', width: '100%', position: 'relative' }}>
            {hoveredStoreName && <div className="absolute top-2 left-1/2 -translate-x-1/2 z-[1000] bg-background/90 p-2 rounded-md shadow-lg text-sm font-semibold">{hoveredStoreName}</div>}
            <style>{markerHtmlStyles}</style>
            <MapContainer center={[-27, 133]} zoom={4} style={{ height: '100%', width: '100%' }}>
                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' />
                <MapViewController bounds={bounds} />
                {stores.map(store => (
                    <StoreMarker key={store.id} store={store} isSelected={selectedStoreIds.has(store.id)} onStoreSelect={onStoreSelect} onMouseOver={setHoveredStoreName} onMouseOut={() => setHoveredStoreName(null)} />
                ))}
            </MapContainer>
        </div>
    );
};

export default React.memo(StoreMap);
```

## frontend/src/page_components/dialog-pages/EditLocationPage.tsx
(Full file — entire component is removed)
```tsx
"use client";

import React, { useState, useCallback, useEffect } from 'react';
import dynamic from 'next/dynamic';
import RadiusSlider from '../../components/RadiusSlider';
import CompanyFilter from '../../components/CompanyFilter';
import StoreList from '../../components/StoreList';
import MultiplePostcodeInput from '../../components/MultiplePostcodeInput';
import { Button } from '../../components/ui/button';
import { useAuth } from '../../context/AuthContext';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Label } from "../../components/ui/label";
import { Input } from "../../components/ui/input";
import { PlusCircle, Save, Trash2, Pencil } from 'lucide-react';
import { useStoreSearch } from '../../context/StoreSearchContext';
import { useStoreList } from '../../context/StoreListContext';
import type { EditLocationPageProps } from '../../types/EditLocationPageProps';

const StoreMap = dynamic(() => import('../../components/StoreMap'), { ssr: false });

const EditLocationPage: React.FC<EditLocationPageProps> = ({ localSelectedStoreIds, setLocalSelectedStoreIds, onOpenChange, setHasSearchOccurred }) => {
  // ... full component as in the original file
  // (see git history for complete implementation)
};

export default EditLocationPage;
```

---

# Store Selection — Frontend Partial Excerpts

## frontend/src/app/providers.tsx
Remove `StoreListProvider` and `StoreSearchProvider` from the tree:
```tsx
// Remove these imports:
import { StoreListProvider } from "@/context/StoreListContext";
import { StoreSearchProvider } from "@/context/StoreSearchContext";

// Remove these wrappers from AppProviders:
<StoreListProvider>
  <StoreSearchProvider>{children}</StoreSearchProvider>
</StoreListProvider>
```

## frontend/src/components/settings-dialog.tsx
Remove the `"Edit Location"` nav item and `EditLocationPage` case from `PageContent`, and remove
all `localSelectedStoreIds` / `setLocalSelectedStoreIds` / `hasSearchOccurred` state and props,
and remove the `useStoreList` import and usage (`selectedStoreIds`, `setSelectedStoreIds`,
`saveStoreList`, `currentStoreListName`). The `handleOpenChange` store-save logic also goes.

## frontend/src/types/index.ts
Lines to remove (re-exports for deleted types):
```ts
export type { SelectedStoreListType } from './SelectedStoreListType';
export type { ActiveStoreListData } from './ActiveStoreListData';
export type { StoreListContextType } from './StoreListContextType';
export type { StoreSearchContextType } from './StoreSearchContextType';
export type { StoreListProps } from './StoreListProps';
export type { StoreMapProps } from './StoreMapProps';
export type { EditLocationPageProps } from './EditLocationPageProps';
export type { SearchParams } from './SearchParams';
export type { NearbyStoresResponse } from './NearbyStoresResponse';
```

## frontend/src/types/Cart.ts
Line 9 — remove store list reference from Cart type:
```ts
selected_store_list?: SelectedStoreListType;
```
Also remove the import: `import type { SelectedStoreListType } from './SelectedStoreListType';`

---

# Type Files — Complete (delete entirely)

- `frontend/src/types/SelectedStoreListType.ts`
- `frontend/src/types/ActiveStoreListData.ts`
- `frontend/src/types/StoreListContextType.ts`
- `frontend/src/types/StoreSearchContextType.ts`
- `frontend/src/types/StoreListProps.ts`
- `frontend/src/types/StoreMapProps.ts`
