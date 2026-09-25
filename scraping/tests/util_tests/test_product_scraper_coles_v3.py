"""`ColesScraperV3` -- the same Coles scrape, fetched in parallel.

v3 exists only to overlap the network waits: it fetches every category on a
thread pool, then cleans and writes them sequentially. That split is the whole
point of the class and also its whole risk, because the file it writes has to
come out in the same order and with the same contents as v2's.

The fetch loop itself is v2's, copied. It is covered there; this file covers
what v3 adds -- the ordering, and what a thread raising does to the run.
"""

import json
from unittest.mock import MagicMock

import pytest

from scraping.scrapers.product_scraper_coles_v3 import ColesScraperV3

STORE_ID = 'coles:1234'


def _browse_page(results, no_of_results=None, page_size=48, store_id='1234'):
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
    response = MagicMock()
    response.text = (
        '<html><body>'
        f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script>'
        '</body></html>'
    )
    response.raise_for_status.return_value = None
    return response


def _scraper(categories):
    command = MagicMock()
    command.style.ERROR.side_effect = lambda message: message
    command.style.SUCCESS.side_effect = lambda message: message
    session_manager = MagicMock()
    session_manager.is_blocked.return_value = False
    scraper = ColesScraperV3(
        command=command,
        company='Coles',
        store_id=STORE_ID,
        store_name='Coles Fremantle',
        state='wa',
        categories_to_fetch=categories,
        session=MagicMock(),
        session_manager=session_manager,
    )
    scraper.jsonl_writer = MagicMock()
    scraper.jsonl_writer.write_product.return_value = True
    scraper.setup = lambda: True
    return scraper


@pytest.fixture
def scraper():
    return _scraper(['dairy', 'bakery', 'frozen'])


def _packet(name):
    return {'metadata': {'company': 'coles'}, 'products': [{'name': name}]}


class TestFetchingInParallel:
    def test_every_category_is_fetched(self, scraper):
        fetched = []
        scraper.fetch_data_for_item = lambda item: fetched.append(item) or [item]
        scraper.clean_raw_data = lambda raw: _packet(raw[0])

        scraper.run()

        assert sorted(fetched) == ['bakery', 'dairy', 'frozen']

    def test_results_are_written_in_the_order_the_categories_were_given(
        self, scraper
    ):
        """Threads finish in whatever order the network allows. The file has to
        come out in category order regardless, or two runs of the same store
        produce different files and every diff between them is noise."""
        scraper.fetch_data_for_item = lambda item: [item]
        scraper.clean_raw_data = lambda raw: _packet(raw[0])

        scraper.run()

        written = [
            call.args[0]['name']
            for call in scraper.jsonl_writer.write_product.call_args_list
        ]
        assert written == ['dairy', 'bakery', 'frozen']

    def test_a_category_that_returned_nothing_is_skipped(self, scraper):
        scraper.fetch_data_for_item = lambda item: [] if item == 'bakery' else [item]
        scraper.clean_raw_data = lambda raw: _packet(raw[0])

        scraper.run()

        written = [
            call.args[0]['name']
            for call in scraper.jsonl_writer.write_product.call_args_list
        ]
        assert written == ['dairy', 'frozen']

    def test_a_completed_run_is_committed(self, scraper):
        scraper.fetch_data_for_item = lambda item: [item]
        scraper.clean_raw_data = lambda raw: _packet(raw[0])

        scraper.run()

        scraper.jsonl_writer.commit.assert_called_once()
        scraper.jsonl_writer.cleanup.assert_not_called()

    def test_a_run_that_found_nothing_is_thrown_away(self, scraper):
        scraper.fetch_data_for_item = lambda item: []

        scraper.run()

        scraper.jsonl_writer.cleanup.assert_called_once()
        scraper.jsonl_writer.commit.assert_not_called()


class TestWhenAThreadFails:
    def test_a_blocked_session_aborts_the_whole_store(self, scraper):
        """`future.result()` re-raises in the main thread on purpose. A CAPTCHA
        wall affects the session, not one category, so the remaining categories
        would all return nothing and the file would be committed short."""

        def fetch(item):
            if item == 'bakery':
                raise InterruptedError('Session appears to be blocked by CAPTCHA.')
            return [item]

        scraper.fetch_data_for_item = fetch
        scraper.clean_raw_data = lambda raw: _packet(raw[0])

        with pytest.raises(InterruptedError):
            scraper.run()

        scraper.jsonl_writer.write_product.assert_not_called()

    def test_a_cleaning_failure_stops_the_writing_loop(self, scraper):
        scraper.fetch_data_for_item = lambda item: [item]

        def clean(raw):
            if raw[0] == 'bakery':
                raise ValueError('cleaner is broken')
            return _packet(raw[0])

        scraper.clean_raw_data = clean

        scraper.run()

        written = [
            call.args[0]['name']
            for call in scraper.jsonl_writer.write_product.call_args_list
        ]
        assert written == ['dairy']


class TestSetup:
    def test_the_output_is_addressed_to_the_barcode_inbox(self, monkeypatch, tmp_path):
        """Same as v2: Coles barcodes are added by a second pass, so this file
        goes to the barcode scraper rather than to the upload outbox."""
        built = {}

        def fake_writer(company, store_name_slug, state, final_outbox_path=None):
            built.update(slug=store_name_slug, outbox=final_outbox_path)
            return MagicMock()

        monkeypatch.setattr(
            'scraping.scrapers.product_scraper_coles_v3.JsonlWriter', fake_writer
        )
        monkeypatch.setattr(
            'scraping.scrapers.product_scraper_coles_v3.settings.BASE_DIR', tmp_path
        )
        scraper = ColesScraperV3(
            command=MagicMock(),
            company='Coles',
            store_id=STORE_ID,
            store_name='Coles Fremantle',
            state='wa',
            categories_to_fetch=[],
            session=MagicMock(),
            session_manager=MagicMock(),
        )

        assert scraper.setup() is True
        assert built['slug'] == 'coles-fremantle-1234'
        assert built['outbox'].endswith('barcode_scraper_inbox')


class TestTheFetchLoopMatchesV2:
    def test_it_reads_the_same_blob_and_pages_the_same_way(self):
        """v3's `fetch_data_for_item` is a copy of v2's. If one is changed and
        the other is not, this is where that shows up."""
        scraper = _scraper(['dairy'])
        scraper.session.get.side_effect = [
            _browse_page([{'n': 1}], no_of_results=3, page_size=1),
            _browse_page([{'n': 2}], no_of_results=3, page_size=1),
            _browse_page([{'n': 3}], no_of_results=3, page_size=1),
        ]

        assert scraper.fetch_data_for_item('dairy') == [{'n': 1}, {'n': 2}, {'n': 3}]

    def test_a_store_that_has_drifted_is_reported_and_not_scraped(self):
        scraper = _scraper(['dairy'])
        scraper.session.get.side_effect = [
            _browse_page([{'name': 'Milk'}], store_id='9999')
        ]

        assert scraper.fetch_data_for_item('dairy') == []
        assert scraper.command.stderr.write.called
