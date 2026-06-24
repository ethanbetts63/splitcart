from unittest.mock import MagicMock

from scraping.scrapers.product_scraper_woolworths import ProductScraperWoolworths


def test_fetch_data_for_item_stamps_canonical_category_path():
    command = MagicMock()
    scraper = ProductScraperWoolworths(
        command=command,
        company='Woolworths',
        store_id='1147',
        store_name='Bass Hill',
        state='nsw',
        categories_to_fetch=[],
    )
    first_response = MagicMock()
    first_response.raise_for_status.return_value = None
    first_response.json.return_value = {
        'Bundles': [
            {'Products': [{'Name': 'Rokeby Probiotic Filmjolk Yoghurt Natural'}]},
        ],
    }
    empty_response = MagicMock()
    empty_response.raise_for_status.return_value = None
    empty_response.json.return_value = {'Bundles': []}
    scraper.session = MagicMock()
    scraper.session.post.side_effect = [first_response, empty_response]

    item = {
        'slug': 'kefir',
        'node_id': '1_1C9F655',
        'category_path': ['Dairy, Eggs & Fridge', 'Yoghurt', 'Kefir'],
    }

    products = scraper.fetch_data_for_item(item)

    assert products == [
        {
            'Name': 'Rokeby Probiotic Filmjolk Yoghurt Natural',
            'category_path': ['Dairy, Eggs & Fridge', 'Yoghurt', 'Kefir'],
        },
    ]
