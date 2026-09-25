"""`ProductScraperAldi.fetch_data_for_item` -- paging the ALDI product API.

ALDI answers 30 products at a time and gives no page count, so the loop has to
work out for itself when a category is finished. Getting that wrong is either a
short scrape (products silently missing from the catalogue) or an endless one.

No request leaves the machine: the session is a `Mock` whose `get` returns
prepared responses, which is how every other HTTP boundary in this app is
tested.
"""

from unittest.mock import MagicMock

import pytest
import requests

from scraping.scrapers.product_scraper_aldi import ProductScraperAldi


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch):
    """The scraper sleeps between pages to be polite to ALDI. A test waiting on
    a real clock is a test nobody runs."""
    monkeypatch.setattr('scraping.scrapers.product_scraper_aldi.time.sleep', lambda _: None)


@pytest.fixture
def scraper():
    command = MagicMock()
    command.style.ERROR.side_effect = lambda message: message
    scraper = ProductScraperAldi(
        command=command,
        company='Aldi',
        store_id='G123',
        store_name='Aldi Fremantle',
        state='wa',
    )
    scraper.session = MagicMock()
    return scraper


def _page(products, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.raise_for_status.return_value = None
    response.json.return_value = {'data': products}
    return response


ITEM = ('fruit-and-veg', 'key-123')


class TestPaging:
    def test_every_page_of_a_category_is_collected(self, scraper):
        scraper.session.get.side_effect = [
            _page([{'name': f'Product {n}'} for n in range(30)]),
            _page([{'name': 'Product 30'}]),
            _page([]),
        ]

        products = scraper.fetch_data_for_item(ITEM)

        assert len(products) == 31
        assert products[-1] == {'name': 'Product 30'}

    def test_the_offset_advances_by_the_page_size(self, scraper):
        """The offset is the only thing distinguishing one request from the
        next; repeating it returns page one forever."""
        scraper.session.get.side_effect = [
            _page([{'name': 'a'}]),
            _page([{'name': 'b'}]),
            _page([]),
        ]

        scraper.fetch_data_for_item(ITEM)

        offsets = [call.kwargs['params']['offset'] for call in scraper.session.get.call_args_list]
        assert offsets == [0, 30, 60]

    def test_the_request_identifies_the_store_and_the_category(self, scraper):
        """Prices are per store. A missing `servicePoint` would silently return
        a different store's catalogue."""
        scraper.session.get.side_effect = [_page([])]

        scraper.fetch_data_for_item(ITEM)

        params = scraper.session.get.call_args.kwargs['params']
        assert params['servicePoint'] == 'G123'
        assert params['categoryKey'] == 'key-123'
        assert params['currency'] == 'AUD'

    def test_an_empty_first_page_returns_nothing_and_stops(self, scraper):
        scraper.session.get.side_effect = [_page([])]

        assert scraper.fetch_data_for_item(ITEM) == []
        assert scraper.session.get.call_count == 1


class TestWhenTheApiRefuses:
    def test_a_400_ends_the_category_without_raising(self, scraper):
        """ALDI answers 400 rather than an empty page once the offset runs past
        the end of a category."""
        scraper.session.get.side_effect = [
            _page([{'name': 'a'}]),
            _page([], status_code=400),
        ]

        products = scraper.fetch_data_for_item(ITEM)

        assert products == [{'name': 'a'}]

    def test_a_network_error_keeps_what_was_already_fetched(self, scraper):
        """One flaky category must not cost the whole store's scrape."""
        scraper.session.get.side_effect = [
            _page([{'name': 'a'}]),
            requests.exceptions.ConnectionError('dropped'),
        ]

        products = scraper.fetch_data_for_item(ITEM)

        assert products == [{'name': 'a'}]
        assert scraper.command.stderr.write.called

    def test_a_body_that_is_not_json_is_reported_not_raised(self, scraper):
        broken = MagicMock()
        broken.status_code = 200
        broken.raise_for_status.return_value = None
        broken.json.side_effect = requests.exceptions.JSONDecodeError('bad', '', 0)
        scraper.session.get.side_effect = [broken]

        assert scraper.fetch_data_for_item(ITEM) == []
        assert scraper.command.stderr.write.called

    def test_an_http_error_ends_the_category(self, scraper):
        failing = MagicMock()
        failing.status_code = 503
        failing.raise_for_status.side_effect = requests.exceptions.HTTPError('503')
        scraper.session.get.side_effect = [failing]

        assert scraper.fetch_data_for_item(ITEM) == []


class TestSetup:
    def test_setup_names_the_output_file_after_the_store(self, scraper, monkeypatch):
        """The filename is how the pipeline attributes prices to a store."""
        built = {}

        def fake_writer(company, store_name_slug, state, **kwargs):
            built['args'] = (company, store_name_slug, state)
            return MagicMock()

        monkeypatch.setattr(
            'scraping.scrapers.product_scraper_aldi.JsonlWriter', fake_writer
        )

        assert scraper.setup() is True
        assert built['args'] == ('Aldi', 'aldi-fremantle-G123', 'wa')

    def test_a_store_with_no_name_still_gets_a_usable_one(self, scraper, monkeypatch):
        built = {}
        monkeypatch.setattr(
            'scraping.scrapers.product_scraper_aldi.JsonlWriter',
            lambda company, slug, state, **kwargs: built.setdefault('slug', slug),
        )
        scraper.store_name = ''

        scraper.setup()

        assert built['slug'] == 'aldi-store-g123-G123'

    def test_setup_sends_a_scraper_that_identifies_itself(self, scraper, monkeypatch):
        """ALDI is entitled to know who is calling and how to reach us."""
        monkeypatch.setattr(
            'scraping.scrapers.product_scraper_aldi.JsonlWriter',
            lambda *args, **kwargs: MagicMock(),
        )

        scraper.setup()

        assert 'splitcart.com' in scraper.session.headers['user-agent']
