
import json
from django.test import TestCase
from api.utils.shop_scraping_utils.iga.parse_and_clean_stores import parse_and_clean_stores

class TestParseAndCleanStores(TestCase):

    def test_parse_and_clean_stores(self):
        store_data_1 = {"id": 1, "name": "IGA Test Store 1", "distance": 10.5}
        store_data_2 = {"id": 2, "name": "IGA Test Store 2", "distance": 20.2}
        html_content = f'''
            <div data-storedata='{json.dumps(store_data_1)}'></div>
            <div data-storedata='{json.dumps(store_data_2)}'></div>
        '''

        stores = parse_and_clean_stores(html_content)

        self.assertEqual(len(stores), 2)
        self.assertNotIn("distance", stores[0])
        self.assertNotIn("distance", stores[1])
        self.assertEqual(stores[0]["name"], "IGA Test Store 1")
        self.assertEqual(stores[1]["name"], "IGA Test Store 2")

    def test_no_store_data(self):
        html_content = "<div>No store data here</div>"
        stores = parse_and_clean_stores(html_content)
        self.assertEqual(len(stores), 0)

    def test_malformed_json(self):
        html_content = '<div data-storedata="{&quot;id&quot;: 1, &quot;name&quot;: &quot;IGA Malformed&quot;}"></div>'
        stores = parse_and_clean_stores(html_content)
        self.assertEqual(len(stores), 0)

    def test_html_unescape(self):
        html_content = '<div data-storedata="{&quot;id&quot;: 1, &quot;name&quot;: &quot;IGA &amp; Co&quot;}"></div>'
        stores = parse_and_clean_stores(html_content)
        self.assertEqual(len(stores), 1)
        self.assertEqual(stores[0]["name"], "IGA & Co")
