"""`ColesScraperV2.fetch_data_for_item` -- reading Coles' browse pages.

Coles has no product API. The scraper asks for the browse page and reads the
`__NEXT_DATA__` blob Next.js leaves in the HTML, which means three things can go
wrong that an API would not have: the blob can be absent, the page can be a
CAPTCHA wall, and the session can silently drift to a different store -- which
would attribute one suburb's prices to another.

Nothing here reaches Coles. The session is a `Mock` returning prepared HTML.
"""

import json
from unittest.mock import MagicMock

import pytest
import requests

from scraping.scrapers.product_scraper_coles_v2 import ColesScraperV2

STORE_ID = 'coles:1234'


def _browse_page(results, no_of_results=None, page_size=48, store_id='1234'):
    """A browse page with the `__NEXT_DATA__` blob Coles actually serves."""
    payload = {
        'props': {
            'pageProps': {
                'initStoreId': store_id,
                'searchResults': {
                    'results': results,
                    'noOfResults': (
                        no_of_results if no_of_results is not None else len(results)
                    ),
                    'pageSize': page_size,
                },
            }
        }
    }
    html = (
        '<html><body>'
        f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script>'
        '</body></html>'
    )
    response = MagicMock()
    response.text = html
    response.raise_for_status.return_value = None
    return response


def _page_without_the_blob():
    response = MagicMock()
    response.text = '<html><body>Nothing here</body></html>'
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def scraper():
    command = MagicMock()
    command.style.ERROR.side_effect = lambda message: message
    session_manager = MagicMock()
    session_manager.is_blocked.return_value = False
    return ColesScraperV2(
        command=command,
        company='Coles',
        store_id=STORE_ID,
        store_name='Coles Fremantle',
        state='wa',
        categories_to_fetch=['fruit-vegetables'],
        session=MagicMock(),
        session_manager=session_manager,
    )


class TestReadingABrowsePage:
    def test_the_products_in_the_blob_are_returned(self, scraper):
        scraper.session.get.side_effect = [
            _browse_page([{'name': 'Milk'}]),
            _browse_page([]),
        ]

        assert scraper.fetch_data_for_item('dairy') == [{'name': 'Milk'}]

    def test_the_category_is_asked_for_by_slug(self, scraper):
        scraper.session.get.side_effect = [_browse_page([])]

        scraper.fetch_data_for_item('dairy-eggs-fridge')

        assert 'browse/dairy-eggs-fridge' in scraper.session.get.call_args.args[0]

    def test_a_page_without_the_blob_ends_the_category(self, scraper):
        """An empty category, or a page shape Coles has changed. Either way
        there is nothing to read and nothing to report as products."""
        scraper.session.get.side_effect = [_page_without_the_blob()]

        assert scraper.fetch_data_for_item('dairy') == []

    def test_a_blob_with_no_results_ends_the_category(self, scraper):
        scraper.session.get.side_effect = [_browse_page([])]

        assert scraper.fetch_data_for_item('dairy') == []


class TestPaging:
    def test_the_page_count_is_taken_from_the_result_total(self, scraper):
        """Coles states how many products a category holds and how many fit on
        a page; the scraper asks for exactly that many pages and no more."""
        scraper.session.get.side_effect = [
            _browse_page([{'n': 1}], no_of_results=5, page_size=2),
            _browse_page([{'n': 2}], no_of_results=5, page_size=2),
            _browse_page([{'n': 3}], no_of_results=5, page_size=2),
        ]

        products = scraper.fetch_data_for_item('dairy')

        assert products == [{'n': 1}, {'n': 2}, {'n': 3}]
        assert scraper.session.get.call_count == 3

    def test_each_page_is_asked_for_by_number(self, scraper):
        scraper.session.get.side_effect = [
            _browse_page([{'n': 1}], no_of_results=3, page_size=1),
            _browse_page([{'n': 2}], no_of_results=3, page_size=1),
            _browse_page([{'n': 3}], no_of_results=3, page_size=1),
        ]

        scraper.fetch_data_for_item('dairy')

        pages = [call.args[0].split('page=')[1] for call in scraper.session.get.call_args_list]
        assert pages == ['1', '2', '3']

    def test_a_category_that_fits_on_one_page_stops_at_the_first_empty_one(
        self, scraper
    ):
        """The page-count guard only engages once Coles reports more than one
        page, so a short category is confirmed finished by an empty page rather
        than by arithmetic. That is one extra request per category -- worth
        knowing, and not worth a behaviour change."""
        scraper.session.get.side_effect = [
            _browse_page([{'n': 1}], no_of_results=1, page_size=48),
            _browse_page([]),
        ]

        assert scraper.fetch_data_for_item('dairy') == [{'n': 1}]
        assert scraper.session.get.call_count == 2


class TestWhenTheSessionIsNoLongerTrustworthy:
    def test_a_captcha_wall_stops_the_run_rather_than_being_scraped(self, scraper):
        """`InterruptedError` is deliberately not caught here: the controlling
        command has to re-establish a session, and carrying on would write a
        CAPTCHA page's worth of nothing into the outbox."""
        scraper.session_manager.is_blocked.return_value = True
        scraper.session.get.side_effect = [_browse_page([{'name': 'Milk'}])]

        with pytest.raises(InterruptedError):
            scraper.fetch_data_for_item('dairy')

    def test_a_store_that_has_drifted_is_reported_and_not_scraped(self, scraper):
        """Coles prices are per store. A session that has quietly switched
        stores would file another suburb's prices under this one."""
        scraper.session.get.side_effect = [
            _browse_page([{'name': 'Milk'}], store_id='9999')
        ]

        products = scraper.fetch_data_for_item('dairy')

        assert products == []
        assert scraper.command.stderr.write.called

    def test_a_network_error_keeps_what_was_already_fetched(self, scraper):
        scraper.session.get.side_effect = [
            _browse_page([{'n': 1}], no_of_results=10, page_size=1),
            requests.exceptions.ConnectionError('dropped'),
        ]

        assert scraper.fetch_data_for_item('dairy') == [{'n': 1}]
        assert scraper.command.stderr.write.called


class TestSetup:
    def test_the_output_is_addressed_to_the_barcode_inbox(self, scraper, monkeypatch, tmp_path):
        """This scraper's file is not finished: Coles barcodes are added by a
        second pass, so the outbox it names is the barcode scraper's inbox."""
        built = {}

        def fake_writer(company, store_name_slug, state, final_outbox_path=None):
            built.update(
                company=company,
                slug=store_name_slug,
                state=state,
                outbox=final_outbox_path,
            )
            return MagicMock()

        monkeypatch.setattr(
            'scraping.scrapers.product_scraper_coles_v2.JsonlWriter', fake_writer
        )
        monkeypatch.setattr(
            'scraping.scrapers.product_scraper_coles_v2.settings.BASE_DIR', tmp_path
        )

        assert scraper.setup() is True
        assert built['slug'] == 'coles-fremantle-1234'
        assert built['outbox'].endswith('barcode_scraper_inbox')

    def test_the_work_items_are_the_categories_it_was_given(self, scraper):
        assert scraper.get_work_items() == ['fruit-vegetables']
